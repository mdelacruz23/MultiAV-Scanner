import shutil

import os.path
from os import path
import pathlib
import errno
import time
import mimetypes
import magic
from pyunpack import Archive, PatoolError

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from functions.common import AV_STATUS_CLEAN
from functions.common import AV_STATUS_INFECTED
from functions.common import AV_UPDATE_TAGS
from functions.common import AV_STATUS_METADATA
from functions.common import AV_SIGNATURE_METADATA
from functions.common import AV_ENGINE_METADATA
from functions.common import AV_TIMESTAMP_METADATA

from functions.common import list_files
from functions.common import get_timestamp
from functions.common import remove_empty_folders
from functions.common import bcolors
from functions.common import get_logger
from functions.common import ARCHIVES

LOG_FILENAME = 'FSmultiav_scan'
LOG_NAME = 'FsScanner-W'

exclude_patterns = ['.swpx', '.swp', '.swo']
excludes = shutil.ignore_patterns(*exclude_patterns)


class WatchEvent(PatternMatchingEventHandler):

    def __init__(self, prefix, patterns, ignore_patterns, ignore_directories, case_sensitive):
        self.prefix = prefix
        # log.debug(f"{bcolors.DEBUG}patterns: {patterns} ignore_patterns: {ignore_patterns}, ignore_directories: {ignore_directories} case_sensitive: {case_sensitive}{bcolors.ENDC}")
        super(WatchEvent, self).__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)

    def on_created(self, event):
        if any(swap in event.src_path for swap in exclude_patterns):
            # skip swap files that are being edited
            return
        log.debug(f"{bcolors.CYAN}created: {event}{bcolors.ENDC}")
        log.debug(f"{bcolors.CYAN}src_path: {event.src_path} prefix: {self.prefix}{bcolors.ENDC}")
        dst_path = os.path.join(self.prefix, event.src_path.strip("/"))
        src_path = event.src_path
        log.debug(f"{bcolors.CYAN}Copy  {src_path} to {dst_path}{bcolors.ENDC}")
        try:
            shutil.copy(src_path, dst_path, follow_symlinks=False)
        except (IOError, IsADirectoryError):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            try:
                shutil.copytree(src_path, dst_path, ignore=excludes, dirs_exist_ok=True)
            except NotADirectoryError:
                shutil.copy(src_path, dst_path)

    def on_deleted(self, event):
        pass
        # log.debug(f"{bcolors.DEBUG} on_deleted {event.src_path}{bcolors.ENDC}")

    def on_modified(self, event):
        if any(swap in event.src_path for swap in exclude_patterns):
            return
        log.debug(f"{bcolors.DEBUG}modified: {event}{bcolors.ENDC}")
        self.on_created(event)

    def on_moved(self, event):
        pass
        # log.debug(f"{bcolors.DEBUG}moved, {event.src_path}{bcolors.ENDC}")


class Watcher:

    def move_file(src_fpath, dest_fpath):
        try:
            if path.exists(src_fpath):
                log.info(f"Moving file from: {src_fpath} to: {dest_fpath}")
                os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
                shutil.copy(src_fpath, dest_fpath)
                log.debug(f"{bcolors.DEBUG} Removing: {src_fpath}{bcolors.ENDC}")
                os.remove(src_fpath)
        except OSError as e:
            log.error(f"{bcolors.FAIL}Error while deleting file {src_fpath} Reason: {e}{bcolors.ENDC}")

    def set_av_tags(fpath, attributes):
        log.info(f"Setting tags: object: {fpath} attribute: {attributes}")
        for attribute, value in attributes.items():
            try:
                os.setxattr(fpath, attribute, bytes(value, 'utf8'))
            except Exception as err:
                if err.errno != errno.EOPNOTSUPP and err.errno != errno.ENOTSUP:
                    log.exception(f"Unexpected error: {err}")
                else:
                    # underlying fs returns EOPNOTSUPP when attempting to set metadata on a file
                    log.warning(f"{bcolors.WARNING}Setting tag metadata to file is not supported{bcolors.ENDC}")
                return 1

    def scan_handler(input_dir, output_dir, infected_dir, prefix, multi_av, cpu_config, speed, sequential):
        scan_files = list_files(prefix)
        if not scan_files:
            log.info("No files to scan")
            return
        else:
            start_scan_time = get_timestamp()
            log.info(f"started scanning at: {start_scan_time}")
            log.debug(f"{bcolors.DEBUG}scan_files: {scan_files}{bcolors.ENDC}")

        for file_path in scan_files:
            try:
                # To get fime mime using magic rather than mimetypes since magic is using
                # a Magic Number for the identification of a file rather than file extension.
                mime_type = magic.from_file(str(file_path), mime=True)
                log.info(f"Object name: {file_path} mime_type: {mime_type}")
                extensions = None
                if mime_type is not None:
                    extensions = mimetypes.guess_all_extensions(mime_type, strict=False)
                if extensions is not None and any(x in extensions for x in ARCHIVES):
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
                log.exception(f'PatoolError: Failure unpacking objects : PatoolError Error: {e} Scan Dir: {prefix} File: {file_path}')
            except Exception as e:
                log.exception(f'Unexpected error occured {e}')

        log.debug(f"{bcolors.DEBUG}calling multi_av.scan. prefix={prefix} speed={speed}{bcolors.ENDC}")
        ret = multi_av.single_scan(prefix, speed) if sequential else multi_av.scan(prefix, speed)
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
                            log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} file_path: {file_path}{bcolors.ENDC}")
                            suffix = pathlib.Path(archive_dir).suffix

                        log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} RESULTS: {results}{bcolors.ENDC}")
                        # for key, val in results.items():
                        #     log.info(f"key: {key} val: {val}")
                        sigs = [val for key, val in results.items() if str(archive_dir) in key]
                        log.debug(f"{bcolors.DEBUG} sigs {sigs} type: {type(sigs)} {bcolors.ENDC}")
                        if type(sigs) == list and sigs:
                            result = sigs[0]
                        else:
                            result = sigs

                        log.debug(f"result: {result} type: {type(result)} ")

                        # for key, val in results.items():
                        #     if archive_dir in key:
                        #         log.info(f"FOUND KEY: {key}")
                        #     else:
                        #         log.info(f"NOT FOUND {archive_dir}")

                        # result = results.get(archive_dir)
                        # log.info(f"archive dir {archive_dir} file_path {file_path} result: {result}")
                    else:
                        result = results.get(str(file_path))
                    log.debug(f"{bcolors.DEBUG}scan_engine: {scan_engine} result: {result} {bcolors.ENDC}")
                    log.info("Parsing result ")
                    if not result:
                        log.info(f"{bcolors.DEBUG}file: {file_path} CLEAN {bcolors.ENDC}")
                        scan_signature.append('OK')
                    else:
                        scan_result = AV_STATUS_INFECTED
                        log.info(f"{bcolors.WARNING}scan_engine: {scan_engine} file: {file_path} INFECTED : {result}  {bcolors.ENDC}")
                        if type(result) is tuple:
                            result = result[1].split()[0]
                            scan_signature.append(result)
                        else:
                            # It's a string
                            result = result.split()[0]
                            scan_signature.append(result)
                    signature = ":".join(scan_signature)
                    log.info(f"{bcolors.DEBUG} scan_engine: {scan_engine} signature: {signature}{bcolors.ENDC}")
                log.info(f" Completed scan of {file_path}")
            except Exception as e:
                log.exception(f"Unexpected error: {e} ")
                return 1
            av_engines = ':'.join(map(str, ret))
            log.info(f"AV engines applied: {av_engines}")
            result_time = get_timestamp()
            if scan_result == AV_STATUS_CLEAN:
                log.info(f"CLEAN OBJECT: {file_path} scan_result: {scan_result} result_time: {result_time}")
                dest_fpath = str(file_path).replace(prefix, '') \
                    .replace(input_dir, '').strip("/")
                dest_fpath = os.path.join(output_dir, dest_fpath)
                src_fpath = str(file_path).replace(prefix, '')
                log.info(f"output_dir: {output_dir} src_fpath: {src_fpath} dest_fpath: {dest_fpath}")
                Watcher.move_file(src_fpath, dest_fpath)
            elif scan_result == AV_STATUS_INFECTED:
                # Move Items with infected  results to infected directory
                dest_fpath = str(file_path).replace(prefix, '') \
                    .replace(input_dir, '').strip("/")
                dest_fpath = os.path.join(infected_dir, dest_fpath)
                src_fpath = str(file_path).replace(prefix, '')
                log.debug(f"{bcolors.DEBUG} output_dir: {output_dir} src_fpath: {src_fpath} dest_fpath: {dest_fpath}{bcolors.ENDC}")
                Watcher.move_file(src_fpath, dest_fpath)
                log.warning(f"{bcolors.WARNING}INFECTED OBJECT: {file_path} scan_result: {scan_result} signature: {signature} result_time: {result_time}{bcolors.ENDC}")
            if AV_UPDATE_TAGS:
                tag_list = {AV_STATUS_METADATA: scan_result,
                            AV_SIGNATURE_METADATA: signature,
                            AV_ENGINE_METADATA: av_engines,
                            AV_TIMESTAMP_METADATA: result_time}
                Watcher.set_av_tags(dest_fpath, tag_list)

            remove_empty_folders(input_dir)
            stop_scan_time = get_timestamp()
            log.info(f"Scanning finished at {stop_scan_time}")

    def process_files(input_dir, output_dir, infected_dir, prefix, multi_av, cpu_conf, av_speed, sequential):
        Watcher.scan_handler(input_dir, output_dir, infected_dir, prefix, multi_av, cpu_conf, av_speed, sequential)
        try:
            if os.path.exists(prefix):
                log.debug(f"{bcolors.DEBUG} Removing: {prefix}{bcolors.ENDC}")
                shutil.rmtree(prefix)
        except OSError:
            # pass
            log.error(f"{bcolors.FAIL}Error while deleting directory {prefix}")

    def start(input_dir, output_dir, infected_dir, prefix, multi_av, cpu_conf, av_speed, sequential, log_level):
        """
        The starter method for watching files.
        """
        patterns = ["*"]
        ignore_patterns = exclude_patterns
        ignore_directories = True
        case_sensitive = True
        event_handler = WatchEvent(prefix, patterns, ignore_patterns, ignore_directories, case_sensitive)
        observer = Observer()
        observer.schedule(event_handler, input_dir, recursive=True)
        observer.start()
        global log
        log = get_logger(LOG_NAME, log_level, LOG_FILENAME)
        log.debug(f"{bcolors.DEBUG}input_dir={input_dir}, output_dir={output_dir}, prefix={prefix} av_speed={av_speed} sequential={sequential}{bcolors.ENDC}")
        try:
            while True:
                Watcher.process_files(input_dir, output_dir, infected_dir, prefix, multi_av, cpu_conf, av_speed, sequential)
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
            log.info('Exiting..')
            observer.join()
