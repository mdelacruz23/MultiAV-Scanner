#!/usr/bin/python3
import logging
import traceback
import json
import argparse
import os
import shutil
import queue
import threading
import time
import os.path
from os import path
import pathlib
import errno
import mimetypes
import magic
from pyunpack import Archive, PatoolError
from kafka import KafkaConsumer, KafkaProducer
from retrying import retry

from pathlib import Path
from kafka.errors import (
    KafkaError, OffsetOutOfRangeError
)
# from json import loads
from configs.kafka_config import Config

from functions.common import AV_SCAN_CONFIG
from functions.common import ARCHIVES
from functions.common import AV_STATUS_CLEAN
from functions.common import AV_STATUS_INFECTED
from functions.common import AV_UPDATE_TAGS
from functions.common import AV_STATUS_METADATA
from functions.common import AV_SIGNATURE_METADATA
from functions.common import AV_ENGINE_METADATA
from functions.common import AV_ENGINE_VERSION_METADATA
from functions.common import AV_MIME_METADATA
from functions.common import AV_TIMESTAMP_METADATA
from functions.common import LOG_DIR
from functions.common import LOG_LEVEL_DEF
from functions.common import BATCH_SIZE
from functions.common import get_logger
from functions.common import get_tmp_dir
from functions.common import bcolors
from functions.common import list_files
from functions.common import get_timestamp
from functions.common import remove_empty_folders
from functions.core import CMultiAV

LOG_FILENAME = 'FSmultiav_scan'
LOG_NAME = 'FsScanner-M'
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
verbose = False
pool = None
cpu_conf = 2
multi_av = None
av_speed = {}
sequential = False


class FSScanners:

    global consumer
    consumer = None

    def __init__(self, log_level, config, input_dir, output_dir, infected_dir, fsprefix, batch_size, cpu_conf, speed, sequential):
        try:
            self.multi_av = CMultiAV() if config is None else CMultiAV(cfg=config)
        except Exception as error:
            print(f"ERROR: Couldn't create CMultiAV instance. Reason: {error}")
            raise error

        self.log = get_logger(LOG_NAME, log_level, LOG_FILENAME)
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.infected_dir = infected_dir
        self.fsprefix = fsprefix
        self.batch_size = batch_size
        self.cpu_conf = cpu_conf
        self.speed = speed
        self.sequential = sequential
        self.bootstrap_server = Config.bootstrap_server
        self.consumer_topic = Config.consumer_topic
        self.producer_topic = Config.producer_topic
        self.consumer = None
        self.producer = None

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_consumer(self):
        """Tries to establish the Kafka consumer connection"""
        try:
            self.log.info("Creating new kafka consumer using brokers: " +
                          str(self.bootstrap_server) + ' and topic ' +
                          self.consumer_topic)
            self.consumer = KafkaConsumer(bootstrap_servers=Config.bootstrap_server + ":" + Config.kafka_port,
                                          auto_offset_reset=Config.auto_offset_reset,
                                          max_poll_records=self.batch_size,
                                          consumer_timeout_ms=5000)
            self.consumer.subscribe([Config.consumer_topic])

        except KeyError as e:
            self.log.error('Missing setting named ' + str(e),
                           {'ex': traceback.format_exc()})
        except Exception as e:
            self.log.error(f"Couldn't initialize kafka consumer for topic {self.consumer_topic} error: {e}",
                           {'ex': traceback.format_exc()})
            raise

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_producer(self):
        """Tries to establish the Kafka producer connection"""
        try:
            self.log.info("Creating new kafka producer using brokers: " +
                          str(self.bootstrap_server) + ' and topic ' +
                          self.producer_topic)

            self.producer = KafkaProducer(bootstrap_servers=Config.bootstrap_server + ":" + Config.kafka_port,
                                          value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        except KeyError as e:
            self.log.error('Missing setting named ' + str(e),
                           {'ex': traceback.format_exc()})
        except Exception as e:
            self.log.error(f"Couldn't initialize kafka producer for topic {self.producer_topic} error: {e}",
                           {'ex': traceback.format_exc()})
            raise

    def _setup_kafka(self):
        '''
        Sets up kafka connections
        '''
        try:
            self._create_consumer()
            self._create_producer()
            self.log.info("Successfully connected to Kafka")
        except KafkaError as err:
            self.log.error(err)
            raise
        except Exception as err:
            self.log.error(err)
            raise

    def run_tasks(self):
        '''
        Set up and run
        '''
        self._setup_kafka()
        self._main_loop()

    def _main_loop(self):
        '''
        Continuous loop that reads from a kafka topic,
        moves files into input dir and scans files
        '''

        while True:
            try:
                self.log.info("Started processing Kafka messages")
                self._get_messages()
                self.log.info('finished worker task')
            except Exception as e:
                self.log.error(f"Exception occured in main loop {e}")
            finally:
                # close kafka connections
                if self.consumer is not None:
                    self.log.info("Closing existing kafka consumer")
                    self.consumer.close()
                    self.consumer = None
                if self.producer is not None:
                    self.log.info("Closing existing kafka producer")
                    self.producer.flush()
                    self.producer.close(timeout=10)
                    self.producer = None

    def _process_files(self, results):
        self.log.debug(f"results: {results}")
        isEmpty = (len(results) == 0)
        if isEmpty:
            self.log.info("No files to scan")
            return
        self.prefix = get_tmp_dir(self.fsprefix)
        self.log.debug(f'Local Prefix: {self.prefix}')
        self._copy_files(results, self.input_dir, self.prefix)
        self._scan_handler(self.input_dir, self.output_dir, self.infected_dir, self.prefix, self.multi_av, self.cpu_conf, self.speed, self.sequential)
        try:
            if os.path.exists(self.prefix):
                self.log.debug(f"{bcolors.DEBUG} Removing: {self.prefix}{bcolors.ENDC}")
                shutil.rmtree(self.prefix)
        except OSError:
            # pass
            self.log.error(f"{bcolors.FAIL}Error while deleting directory {self.prefix}")

    def _scan_handler(self, input_dir, output_dir, infected_dir, prefix, multi_av, cpu_config, speed, sequential):
        scan_files = list_files(prefix)
        if not scan_files:
            self.log.info("No files to scan")
            return
        else:
            start_scan_time = get_timestamp()
            self.log.info(f"started scanning at: {start_scan_time}")
            self.log.debug(f"{bcolors.DEBUG}Scanning Files: {scan_files}{bcolors.ENDC}")

        for file_path in scan_files:
            try:
                # To get fime mime using magic rather than mimetypes since magic is using
                # a Magic Number for the identification of a file rather than file extension.
                mime_type = magic.from_file(str(file_path), mime=True)
                self.log.info(f"Object name: {file_path} mime_type: {mime_type}")
                extensions = None
                if mime_type is not None:
                    extensions = mimetypes.guess_all_extensions(mime_type, strict=False)
                if extensions is not None and any(x in extensions for x in ARCHIVES):
                    suffix = pathlib.Path(file_path).suffix
                    archive_dir = file_path
                    self.log.debug(f"{bcolors.DEBUG} suffix: {suffix}{bcolors.ENDC}")
                    while any(x in suffix for x in ARCHIVES):
                        archive_dir = str(archive_dir).removesuffix(suffix)
                        self.log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} file_path: {file_path}{bcolors.ENDC}")
                        suffix = pathlib.Path(archive_dir).suffix
                    self.log.info(f"detected archive file  prefix: {prefix} archive_dir: {archive_dir} file: {file_path}")
                    os.makedirs(archive_dir, exist_ok=True)
                    Archive(file_path).extractall(archive_dir)
                    os.remove(file_path)
            except PatoolError as e:
                self.log.exception(f'PatoolError: Failure unpacking objects : PatoolError Error: {e} Scan Dir: {prefix} File: {file_path}')
            except Exception as e:
                self.log.exception(f'Unexpected error occured {e}')

        self.log.debug(f"{bcolors.DEBUG}calling multi_av.scan. prefix={prefix} speed={speed}{bcolors.ENDC}")
        ret = multi_av.single_scan(prefix, speed) if sequential else multi_av.scan(prefix, speed)
        scan_engine_version = multi_av.versions()
        for file_path in scan_files:
            try:
                scan_signature = []
                scan_result = AV_STATUS_CLEAN
                for scan_engine in ret:
                    results = ret[scan_engine]
                    suffix = pathlib.Path(file_path).suffix
                    archive_dir = file_path
                    if suffix is not None and any(x in suffix for x in ARCHIVES):
                        while any(x in suffix for x in ARCHIVES):
                            archive_dir = str(archive_dir).removesuffix(suffix)
                            self.log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} file_path: {file_path}{bcolors.ENDC}")
                            suffix = pathlib.Path(archive_dir).suffix

                        self.log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} RESULTS: {results}{bcolors.ENDC}")
                        # for key, val in results.items():
                        #     self.log.info(f"key: {key} val: {val}")
                        sigs = [val for key, val in results.items() if str(archive_dir) in key]
                        self.log.info(f"{bcolors.DEBUG} sigs {sigs} type: {type(sigs)} {bcolors.ENDC}")
                        if type(sigs) == list and sigs:
                            result = sigs[0]
                        else:
                            result = sigs

                        self.log.debug(f"result: {result} type: {type(result)} ")

                        # for key, val in results.items():
                        #     if archive_dir in key:
                        #         self.log.info(f"FOUND KEY: {key}")
                        #     else:
                        #         self.log.info(f"NOT FOUND {archive_dir}")

                        # result = results.get(archive_dir)
                        # self.log.info(f"archive dir {archive_dir} file_path {file_path} result: {result}")
                    else:
                        result = results.get(str(file_path))
                    self.log.debug(f"{bcolors.DEBUG}scan_engine: {scan_engine} result: {result} {bcolors.ENDC}")
                    self.log.info("Parsing result ")
                    if not result:
                        self.log.info(f"{bcolors.DEBUG}file: {file_path} CLEAN {bcolors.ENDC}")
                        scan_signature.append('OK')
                    else:
                        scan_result = AV_STATUS_INFECTED
                        self.log.info(f"{bcolors.WARNING}scan_engine: {scan_engine} file: {file_path} INFECTED : {result}  {bcolors.ENDC}")
                        if type(result) is tuple:
                            result = result[1].split()[0]
                            scan_signature.append(result)
                        else:
                            # It's a string
                            result = result.split()[0]
                            scan_signature.append(result)
                    signature = ":".join(scan_signature)
                    self.log.info(f"{bcolors.DEBUG} scan_engine: {scan_engine} signature: {signature}{bcolors.ENDC}")
                self.log.info(f" Completed scan of {file_path}")
            except Exception as e:
                self.log.exception(f"Unexpected error: {e} ")
                return 1
            av_engines = ':'.join(map(str, ret))
            self.log.info(f"AV engines applied: {av_engines}")
            result_time = get_timestamp()
            if scan_result == AV_STATUS_CLEAN:
                self.log.info(f"CLEAN OBJECT: {file_path} scan_result: {scan_result} result_time: {result_time}")
                dest_fpath = str(file_path).replace(prefix, '') \
                    .replace(input_dir, '').strip("/")
                dest_fpath = os.path.join(output_dir, dest_fpath)
                src_fpath = str(file_path).replace(prefix, '')
                self.log.info(f"Moving file src_fpath: {src_fpath} dest_fpath: {dest_fpath}")
                self._move_file(src_fpath, dest_fpath)
            elif scan_result == AV_STATUS_INFECTED:
                # Move Items with infected  results to infected directory
                dest_fpath = str(file_path).replace(prefix, '') \
                    .replace(input_dir, '').strip("/")
                dest_fpath = os.path.join(infected_dir, dest_fpath)
                src_fpath = str(file_path).replace(prefix, '')
                self.log.debug(f"{bcolors.DEBUG} output_dir: {output_dir} src_fpath: {src_fpath} dest_fpath: {dest_fpath}{bcolors.ENDC}")
                self._move_file(src_fpath, dest_fpath)
                self.log.warning(f"{bcolors.WARNING}INFECTED OBJECT: {file_path} scan_result: {scan_result} signature: {signature} result_time: {result_time}{bcolors.ENDC}")
            if AV_UPDATE_TAGS:
                engine_versions = ""
                for key, value in scan_engine_version.items():
                    if engine_versions == "":
                        engine_versions += value
                    else:
                        engine_versions = " :: ".join([engine_versions, value])
                tag_list = {"Topic": self.producer_topic,
                            "filename": os.path.basename(dest_fpath),
                            "absolute-path": os.path.dirname(dest_fpath),
                            AV_STATUS_METADATA: scan_result,
                            AV_SIGNATURE_METADATA: signature,
                            AV_ENGINE_METADATA: av_engines,
                            AV_ENGINE_VERSION_METADATA: engine_versions,
                            AV_MIME_METADATA: mime_type,
                            AV_TIMESTAMP_METADATA: result_time}
                # self._set_av_tags(dest_fpath, tag_list)
                self.log.info(f"Tag List: {tag_list} -- type: {type(tag_list)}")
                self._message_to_kafka(tag_list)
            remove_empty_folders(input_dir)
            stop_scan_time = get_timestamp()
            self.log.info(f"Scanning finished at {stop_scan_time}")

    def _move_file(self, src_fpath, dest_fpath):
        try:
            if path.exists(src_fpath):
                self.log.info(f"Moving file from: {src_fpath} to: {dest_fpath}")
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                # shutil.copy(src_fpath, dest_fpath)
                shutil.move(src_fpath, dest_fpath)
                self.log.debug(f"{bcolors.DEBUG} Removing: {src_fpath}{bcolors.ENDC}")
                # os.remove(src_fpath)
        except OSError as e:
            self.log.error(f"{bcolors.FAIL}Error while deleting file {src_fpath} Reason: {e}{bcolors.ENDC}")

    def _set_av_tags(self, fpath, attributes):
        self.log.debug(f"Setting tags: object: {fpath} attribute: {attributes}")
        for attribute, value in attributes.items():
            try:
                os.setxattr(fpath, attribute, bytes(value, 'utf8'))
            except Exception as err:
                if err.errno != errno.EOPNOTSUPP and err.errno != errno.ENOTSUP:
                    self.log.exception(f"Unexpected error: {err}")
                else:
                    # underlying fs returns EOPNOTSUPP when attempting to set metadata on a file
                    self.log.warning(f"{bcolors.WARNING}Setting tag metadata to file is not supported{bcolors.ENDC}")
                return 1

    def _copy_files(self, results, input_dir, prefix):
        if results is None:
            self.debug.info("No files to scan")
            return

        threads = []
        my_queue = queue.Queue()
        self.log.info(f"Numebr of results: {len(results)}")
        for result in results:
            result = json.loads(result)
            self.log.info(f"result: {result} filename: {result['filename']}")
            absolute_path = result['absolute.path']
            filename = result['filename']
            file_path = absolute_path + filename
            self.log.debug(f"file_path: {file_path} input_dir: {input_dir} prefix: {prefix} ")
            if file_path is not None:
                t = threading.Thread(target=self._copy_file, args=(file_path, input_dir, prefix, my_queue))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        downloads = []
        while not my_queue.empty():
            downloads.append(my_queue.get())

        self.log.debug(f"{bcolors.DEBUG}downloads: {downloads}{bcolors.ENDC}")
        if not downloads:
            return

    def _copy_file(self, src_path, input_dir, prefix, my_queue):
        dst = input_dir
        try:
            shutil.copy(src_path, dst)
            self.log.debug(f"copy file from: {src_path} to: {dst} successful")
        except shutil.SameFileError as e:
            # this is to skip messages for files that were processed before
            # and FS scanners reset occured before kafka messages expired
            self.log.info(f"file copy from {src_path} to {dst} failed due to: {e}")
            pass
        except shutil.Error as e:
            self.log.info(f"shutil exception: copy file from {src_path} to {dst} failed due to: {e}")
            pass
        except Exception as e:
            self.log.error(f"copy 1 file from {src_path} to {dst} failed due to: {e}")
        try:
            # Note: copy needs to be done twice here since file in scan dir is unpacked
            # and its original (packaged) content gone
            dst = os.path.join(prefix, src_path.strip("/"))
            self.log.debug(f"copy file from: {src_path} to: {dst}")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src_path, dst)
        except shutil.SameFileError:
            # skip messages for files that were processed before
            # and FS scanners reset occured before kafka messages expired
            pass
        except shutil.Error:
            pass
        except IOError as io_err:
            self.log.debug(f"create dir failed. error: {io_err}")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src_path, dst)
        except Exception as e:
            self.log.error(f"file copy from {src_path} to {dst} failed due to: {e}")

    def _get_messages(self):

        while True:
            time.sleep(3)
            self.log.info(f"Polling Kafka for topic: {self.consumer_topic} batch size: {self.batch_size}")
            results = []
            try:
                for message in self.consumer:
                    isEmpty = (len(message) == 0)
                    if isEmpty or None:
                        self.log.info("No files to scan")
                        return
                    self.log.debug(f"Successfully poll a record from Kafka topic: {message.topic}")
                    try:
                        msg_value = message.value
                        msg_value = msg_value.decode()
                        self.log.info(f"Message: {msg_value}")
                        results.append(msg_value)
                    except ValueError:
                        extras = {}
                        extras['parsed'] = False
                        extras['valid'] = False
                        extras['data'] = msg_value
                        self.log.warning('Unparseable JSON Received from kafka',
                                         extra=extras)
                    if len(results) == self.batch_size:
                        self.log.info(f"processing full batch: {results}")
                        self._process_files(results)
                        results = []
                if len(results):
                    self.log.info(f"processing partial batch: {len(results)} files: {results}")
                    self._process_files(results)
            except OffsetOutOfRangeError as e:
                # consumer has no idea where they are
                self.consumer.seek_to_end()
                self.log.error(f"Kafka offset out of range error {e}")
            except Exception as e:
                self.log.error(f"error occured while getting kafka messages {e}",
                               {'ex': traceback.format_exc()})
                raise

    def _message_to_kafka(self, item):
        try:
            self.log.info(f"Sending json to kafka topic {self.producer_topic}")
            self.producer.send(self.producer_topic, value=item)
            # self.producer.flush()
        except Exception as e:
            self.log.error(f"Lost connection to Kafka due to: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="scan a specified directory for infected files.")
    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument("-i", "--input", type=str, default=(Config.input_path), help="input directory path")
    required_named.add_argument("-o", "--output", type=str, default=(Config.output_path), help="output directory path")
    required_named.add_argument("-t", "--tainted", type=str, default=(Config.infected_path), help="infected directory path")
    required_named.add_argument("-p", "--prefix", default=(Config.prefix), help="folder")
    required_named.add_argument("-c", "--config", type=str, default=AV_SCAN_CONFIG, help="config path to scan engines used")
    required_named.add_argument("-b", "--batch", default=(BATCH_SIZE), type=int, help="max batch size")
    required_named.add_argument("-s", "--sequential", default=False, help="Run AV scanners in sequential mode")
    required_named.add_argument("-e", "--engine", default='ALL', type=str, choices=['ALL', 'SLOW', 'MEDIUM', 'FAST', 'ULTRA'], help="AV engine selection")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output
    infected_dir = args.tainted
    prefix = args.prefix
    batch_size = int(args.batch)
    config = args.config
    global verbose
    global log
    engine = args.engine.upper()
    sequential = args.sequential
    verbose = args.verbose
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = LOG_LEVEL_DEF

    print('log_level: {log_level}')
    log = get_logger(LOG_NAME, log_level, LOG_FILENAME)
    av_speed = dict(ALL=3, SLOW=2, MEDIUM=1, FAST=0, ULTRA=-1)
    speed = av_speed.get(engine, 3)

    # Set umask
    mask = 0o077
    os.umask(mask)
    try:
        os.makedirs(prefix, exist_ok=True)
        log.info(f"created prefix directory: {prefix}")
    except Exception as e:
        log.error(f"FS scanner create directory failed error; {e}")
        raise
        return 1

    global cpu_conf
    cpu_conf = os.cpu_count()
    log.info(f'Number of configured CPUs: {cpu_conf}')
    log.info(f'input directory: {input_dir}')
    log.info(f'output directory: {output_dir}')
    log.info(f'infected directory: {infected_dir}')
    log.info(f"speed: {speed}  sequential: {sequential}")
    log.info(f'Prefix: {prefix}')
    log.info(f'Batch: {batch_size}')
    log.info(f'Config path: {config}')

    try:
        worker = FSScanners(log_level, config, input_dir, output_dir, infected_dir, prefix, batch_size, cpu_conf, speed, sequential)
    except Exception as e:
        log.error(f"FS scanner initialization error; {e}")
        raise
        return 1
    log.info(f"input_dir={input_dir}, output_dir={output_dir}, prefix={prefix}")
    ret = worker.run_tasks()
    return ret


if __name__ == '__main__':
    main()
