#!/usr/bin/python3
import logging
import traceback
import argparse
import boto3
import botocore.config as boto_config
from botocore.exceptions import ClientError, ParamValidationError
import os
import shutil
import json
from pathlib import Path
import threading
import queue
import time
import mimetypes
import magic
import pathlib
import os.path

from pyunpack import Archive, PatoolError
from functions.scan import scan_handler, get_local_path, verify_s3_object_version, str_to_bool
from functions.scan import event_object
from functions.scan import deleteSQSNotification
from functions.common import AWS_DEFAULT_REGION
from functions.common import AV_SCAN_CONFIG
from functions.common import AV_PROCESS_ORIGINAL_VERSION_ONLY
from functions.common import INFECTED_BUCKET
from functions.common import INPUT_SQS_PATH
from functions.common import OUTPUT_SQS_PATH
from functions.common import S3_PREFIX
from functions.common import BATCHING_TIME
from functions.common import BATCH_SIZE
from functions.common import S3_MAX_POOL_CONNECTIONS
from functions.common import create_dir
from functions.common import get_timestamp
from functions.common import get_tmp_dir
from functions.common import bcolors
from functions.common import LOG_DIR
from functions.common import LOG_LEVEL_DEF
from functions.common import ARCHIVES
from functions.common import SQS_URI
from functions.common import AWS_TLS_CA_BUNDLE
from functions.common import AWS_CERT_VERIFY
from functions.common import S3_URI
from functions.common import SCANNER_LOCK
# from functions.common import MVS_NOTIFY_SLACK
# from functions.slack_notify import slack_notify
from functions.common import get_logger
from functions.core import CMultiAV
LOG_FILENAME = 'S3multiav_scan'
LOG_NAME = 'S3Scanner-M'

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

verbose = False
pool = None
s3_client = None
sqs_client = None
s3_resource = None
cpu_conf = 2
multi_av = None
av_speed = {}

log = None
KB = 1024
MB = 1024**2
GB = 1024**3


class S3Scanners(object):
    def __init__(self, config_file=None):
        '''Initialize S3 scanners
        Error out if initializing S3 client fails
        or creating CMultiAV instance fails

        :param config_file: The CMultiAV yaml config file
        :raises Exception in case of failures
        Note: AWS_TLS_CA_BUNDLE needs to be defined if deployment needs to limit trusted CA
        Location of AWS_TLS_CA_BUNDLE can be diffrent in each deployment
        therefore it should be set based on python -c "import ssl; print(ssl.get_default_verify_paths())"
        output to see where is cafile located
        '''
        try:
            global s3_client
            global s3_resource
            global sqs_client
            if AWS_TLS_CA_BUNDLE is not None:
                s3_client = boto3.client(
                            's3',
                            region_name=AWS_DEFAULT_REGION,
                            endpoint_url=S3_URI,
                            verify=AWS_CERT_VERIFY,
                            config=boto_config.Config(
                                max_pool_connections=S3_MAX_POOL_CONNECTIONS))
                sqs_client = boto3.client(
                             'sqs',
                             region_name=AWS_DEFAULT_REGION,
                             verify=AWS_CERT_VERIFY,
                             endpoint_url=SQS_URI)
            else:
                s3_client = boto3.client(
                            's3',
                            region_name=AWS_DEFAULT_REGION,
                            endpoint_url=S3_URI,
                            verify=AWS_CERT_VERIFY,
                            config=boto_config.Config(
                                max_pool_connections=S3_MAX_POOL_CONNECTIONS))
                sqs_client = boto3.client(
                             'sqs',
                             region_name=AWS_DEFAULT_REGION,
                             endpoint_url=SQS_URI,
                             verify=AWS_CERT_VERIFY)
            s3_resource = boto3.resource('s3')
        except (ClientError, ParamValidationError) as error:
            log.exception("Couldn't create AWS clients")
            raise error
        try:
            global multi_av
            multi_av = CMultiAV() if config_file is None else CMultiAV(cfg=config_file)
        except Exception as error:
            log.exception("Couldn't create CMultiAV instance")
            raise error

    def list_files(self, path):
        print("files in %s" % path)
        for root, dirs, files in os.walk(path):
            for filename in files:
                print(filename)

    def getSQSMessage(self, input_sqs_queue, sqs_client):
        response = sqs_client.receive_message(
            QueueUrl=input_sqs_queue,
            AttributeNames=[

            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=180,
            WaitTimeSeconds=5
        )
        if 'Messages' in response:
            log.debug(f"{bcolors.DEBUG}sqs message: {response} type: {type(response)}{bcolors.ENDC}")
            num_messages = len(response['Messages'])
            for message in response['Messages']:
                body = message['Body']
                # log.debug(f"Body: {body}")
                if 'Records' in body:
                    data = json.loads(body)
                    num = len(data['Records'])
                    # log.debug(f"Data: {data['Records']}")
                    for record in data['Records']:
                        log.debug(f"Record: {record} Record Type: {type(record)}")
                        # bucket = record['s3']['bucket']['name']
                        # key = record['s3']['object']['key']
                        # kv.extend(bucket,key)
                        # log.debug(f"bucket: (bucket) key: (key) KV: (kv)")
                    # kv.append(body)
                    log.debug(f"{bcolors.DEBUG}The number of records in sqs message is:{num}{bcolors.ENDC}")
                else:
                    log.debug(f"{bcolors.DEBUG}There are no records attached to this sqs message: {response}.{bcolors.ENDC}")
                    deleteSQSNotification(sqs_client, message, input_sqs_queue)
            return num_messages, response
        else:
            log.debug(f"{bcolors.DEBUG}No S3 notification. Message: {response} {bcolors.ENDC}")
        return 0

    def download_file(self, sqs_client, s3_resource, s3_client, input_sqs_queue, message, event, out_queue):
        try:
            # Get some environment variables
            EVENT_SOURCE = os.getenv("EVENT_SOURCE", "S3")

            s3_object, object_size = event_object(event, s3_resource, event_source=EVENT_SOURCE)
            if s3_object is None:
                log.error("No objects found in SQS message")
                return 1
            else:
                # delete message
                try:
                    log.warning(f"{bcolors.DEBUG}Deleting SQS message from queue: {input_sqs_queue} message: {event} {bcolors.ENDC}")
                    deleteSQSNotification(sqs_client, message, input_sqs_queue)
                except Exception as e:
                    tb = traceback.format_stack(limit=7)
                    log.error(f"{bcolors.FAIL}Error while deleting message {message} from sqs queue {input_sqs_queue} reason: {e} \n \
                    Traceback: {str(tb)} bcolors.ENDC")
                    return 1
            total, used, free = shutil.disk_usage("/tmp")
            total = round((total / MB), 2)
            used = round((used / MB), 2)
            free = round((free / MB), 2)
            object_size_mb = round((object_size / MB), 2)
            z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
            z_log.debug(f"{bcolors.DEBUG}space on device: Total: {total}  MB Used: {used}  MB Free: {free} MB s3 object size: {object_size_mb} MB {bcolors.ENDC}")
            if free < object_size_mb:
                z_log.error(f"{bcolors.FAIL}Not enough space left on device: Total: {total}  MB Used: {used}  MB Free: {free} MB s3 object size: {object_size_mb} MB {bcolors.ENDC}")
                self.list_files("/tmp")
                return
            if str_to_bool(AV_PROCESS_ORIGINAL_VERSION_ONLY):
                verify_s3_object_version(s3_resource, s3_object)

            file_path = get_local_path(s3_object, prefix)

            z_log.info(f"{bcolors.DEBUG}Downloading file: {file_path} {bcolors.ENDC}")
            scan_dir = os.path.dirname(file_path)
            create_dir(scan_dir)
            z_log.debug(f"Scan dir: {scan_dir}")
            try:
                z_log.info(f"bucket: {s3_object.bucket_name} key: {s3_object.key}")
                s3_client.download_file(s3_object.bucket_name, s3_object.key, file_path)
                # To get file mime using magic rather than mimetypes since magic is using
                # a Magic Number for the identification of a file rather than file extension.
                mime_type = magic.from_file(file_path, mime=True)
                object_size_gb = round((object_size / GB), 2)
                z_log.info(f"Object name: {s3_object.key} Size: {object_size_gb} GB mime_type: {mime_type}")

                # slack_notify is called in scan.py
                # if MVS_NOTIFY_SLACK and object_size_gb >= 2:
                #     input_queue = os.path.basename(input_sqs_queue)
                #     slack_notify(s3_object, object_size_gb, mime_type, input_queue, z_log)
            except OSError as e:
                # we checked for available space before, yet some zipp exploded and
                # this is a transient error on this file system due to "No space left on device"
                # we can skip this download for now and we will pick it up later
                exception_type = type(e).__name__
                tb = traceback.format_stack(limit=5)
                z_log.error(f'Exception {exception_type} occured while getting objects. This is a transient error: Error: {e} BUCKET: {s3_object.bucket_name} Object: {s3_object.key}\n \
                                Traceback: {str(tb)}')
                return 1
            except Exception as e:
                exception_type = type(e).__name__
                tb = traceback.format_stack(limit=5)
                z_log.critical(f'Exception {exception_type} occured while getting objects. Deleting message: Client Error: {e} BUCKET: {s3_object.bucket_name} Object: {s3_object.key}\n \
                                Traceback: {str(tb)}')
                try:
                    deleteSQSNotification(sqs_client, message, input_sqs_queue)
                except Exception as e:
                    log.critical(f'Failure deleting message: {e}')
                return 1

            try:
                extensions = None
                if mime_type is not None:
                    extensions = mimetypes.guess_all_extensions(mime_type, strict=False)
                if extensions is not None and any(x in extensions for x in ARCHIVES):
                    z_log.info(f"detected archive file dir: {scan_dir} file: {file_path}")
                    suffix = pathlib.Path(file_path).suffix
                    archive_dir = file_path
                    log.debug(f"{bcolors.DEBUG} suffix: {suffix}{bcolors.ENDC}")
                    while any(x in suffix for x in ARCHIVES):
                        archive_dir = str(archive_dir).removesuffix(suffix)
                        log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} file_path: {file_path}{bcolors.ENDC}")
                        suffix = pathlib.Path(archive_dir).suffix
                    log.info(f"detected archive file  prefix: {prefix} archive_dir: {archive_dir} file: {file_path}")
                    os.makedirs(archive_dir, exist_ok=True)
                    Archive(file_path).extractall(archive_dir)
                    os.remove(file_path)
            except PatoolError as e:
                tb = traceback.format_stack(limit=5)
                log.error(f'PatoolError: Failure unpacking objects : PatoolError Error: {e} Scan Dir: {scan_dir} File: {file_path}\n \
                                Traceback: {str(tb)}')
            except Exception as e:
                tb = traceback.format_stack(limit=5)
                log.error(f'Unexpected error occured {e} \n \
                    Traceback: {str(tb)}')

            return out_queue.put((file_path, message, EVENT_SOURCE, mime_type))

        except Exception as e:
            tb = traceback.format_stack(limit=5)
            log.error(f'Unexpected error occured {e} \n \
                   Traceback: {str(tb)}')
            return 1

    def processFiles(self, sqs_client, s3_resource, s3_client, input_sqs_queue, output_sqs_queue, batch_size, multi_av, speed, sequential):
        results = self.getSQSMessages(sqs_client, input_sqs_queue, batch_size)
        log.info(f"{bcolors.DEBUG}Number of files to process: {len(results)}{bcolors.ENDC}")
        if len(results) == 0:
            log.info("No files to scan")
            return
        global prefix
        prefix = get_tmp_dir(s3prefix)
        log.info(f'Local Prefix: {prefix}')
        self.downloadFiles(results, sqs_client, s3_resource, s3_client, input_sqs_queue, output_sqs_queue, multi_av, speed, sequential)

    def getSQSMessages(self, sqs_client, input_sqs_queue, batch_size):
        results = []
        start = time.time()
        while len(results) < batch_size and int(time.time() - start) < BATCHING_TIME:
            result = self.getSQSMessage(input_sqs_queue, sqs_client)
            if type(result) is tuple:
                results.append(result)
            elif result == 0:
                time.sleep(1)
                continue
            else:
                log.warning(f"Unknown return: {result}")

        return results

    def downloadFiles(self, results, sqs_client, s3_resource, s3_client, input_sqs_queue, output_sqs_queue, multi_av, speed, sequential):
        threads = []
        my_queue = queue.Queue()
        log.debug(f"Numebr of results: {len(results)}")
        for i in range(len(results)):
            for j in range(results[i][0]):
                message = results[i][1]
                if message is not None:
                    if 'Messages' in message:
                        message = message['Messages'][j]
                        if 'Body' in message:
                            event = message['Body']
                            t = threading.Thread(target=self.download_file, args=(sqs_client, s3_resource, s3_client, input_sqs_queue, message, event, my_queue))
                            threads.append(t)
                            t.start()

        for t in threads:
            t.join()

        downloads = []
        while not my_queue.empty():
            downloads.append(my_queue.get())

        log.debug(f"{bcolors.DEBUG}downloads: {downloads}{bcolors.ENDC}")
        if not downloads:
            return
        start_scan_time = get_timestamp()
        log.info(f"Scanning started at {start_scan_time}")
        scan_handler(downloads, prefix, cpu_conf, sqs_client, s3_resource, s3_client, input_sqs_queue, output_sqs_queue, multi_av, speed, sequential)
        try:
            log.debug(f"Removing: {prefix}")
            shutil.rmtree(prefix)
        except OSError as e:
            # pass
            log.error(f"{bcolors.FAIL}Error: {e} - while deleting directory {prefix} {bcolors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Clamav scan an S3 bucket for infected files.")
    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument("-q", "--sqs", type=str, default=(INPUT_SQS_PATH), help="input sqs event notification queue")
    required_named.add_argument("-o", "--output", type=str, default=(OUTPUT_SQS_PATH), help="output sqs event notification queue")
    required_named.add_argument("-i", "--infected", type=str, default=(INFECTED_BUCKET), help="infected bucket name")
    required_named.add_argument("-p", "--prefix", type=str, default=(S3_PREFIX), help="folder")
    required_named.add_argument("-c", "--config", type=str, default=AV_SCAN_CONFIG, help="config path to scan engines used")
    required_named.add_argument("-b", "--batch", default=(BATCH_SIZE), type=int, help="max batch size")
    required_named.add_argument("-s", "--sequential", default=False, help="Run AV scanners in sequential mode")
    required_named.add_argument("-e", "--engine", default='ALL', type=str, choices=['ALL', 'SLOW', 'MEDIUM', 'FAST', 'ULTRA'], help="AV engine selection")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    input_sqs_queue = args.sqs
    output_sqs_queue = args.output
    infected_bucket = args.infected
    global s3prefix
    s3prefix = args.prefix
    batch_size = int(args.batch)
    config = args.config

    global prefix
    global verbose
    global av_speed
    global log_level
    mask = 0o077
    os.umask(mask)
    create_dir(s3prefix)

    engine = args.engine.upper()
    speed = av_speed.get(engine, 3)
    sequential = args.sequential
    verbose = args.verbose
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = LOG_LEVEL_DEF

    global log
    log = get_logger(LOG_NAME, log_level, LOG_FILENAME)
    av_speed = dict(ALL=3, SLOW=2, MEDIUM=1, FAST=0, ULTRA=-1)

    log.info(f'AWS_CERT_VERIFY: {AWS_CERT_VERIFY}')
    log.info(f'sqs input notification queue: {input_sqs_queue}')
    log.info(f'sqs output notification queue: {output_sqs_queue}')
    log.info(f'Infected bucket name: {infected_bucket}')
    log.info(f"speed: {speed}  sequential: {sequential}")
    log.info(f'Batch: {batch_size}')
    log.info(f'Config path: {config}')
    log.info(f'S3 Prefix: {s3prefix}')

    global cpu_conf
    cpu_conf = os.cpu_count()
    log.info(f'Number of configured CPUs: {cpu_conf}')

    s3_scanners = S3Scanners(config)

    while True:
        # WARNING: Environment variables used by processes running in monit environment
        # is locked and cannot be changed during MVS execution.
        # File is used here as a switch to control on/off scanning.
        SCANNER_LOCKED = os.path.exists(SCANNER_LOCK)
        if SCANNER_LOCKED is False:
            # scan enabled
            s3_scanners.processFiles(sqs_client, s3_resource, s3_client, input_sqs_queue, output_sqs_queue, batch_size, multi_av, speed, sequential)
        else:
            # scan disabled
            log.warning(f'{bcolors.WARNING}Scanner locked >>> Remove {SCANNER_LOCK} to unlock{bcolors.ENDC}')
            time.sleep(10)
    return 0


if __name__ == '__main__':
    main()
