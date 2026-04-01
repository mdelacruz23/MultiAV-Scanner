# -*- coding: utf-8 -*-

import errno
import datetime
import subprocess
import sys
import os
import shutil
import tempfile
import os.path
import stat
from distutils.util import strtobool
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler
import urllib.request
FORMATTER = logging.Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(funcName)s -> %(message)s')
AV_SCAN_CONFIG = "/app/scanners/functions/config.cfg"
AV_SCAN_START_SNS_ARN = os.getenv("AV_SCAN_START_SNS_ARN")
AV_SCAN_START_METADATA = os.getenv("AV_SCAN_START_METADATA", "av-scan-start")
AV_SIGNATURE_METADATA = "av-signatures"
AV_SIGNATURE_OK = "OK"
AV_SIGNATURE_UNKNOWN = "UNKNOWN"
AV_STATUS_CLEAN = os.getenv("AV_STATUS_CLEAN", "CLEAN")
AV_STATUS_INFECTED = os.getenv("AV_STATUS_INFECTED", "INFECTED")
AV_STATUS_ERROR = os.getenv("AV_STATUS_ERROR", "ERROR")
AV_ENGINE_METADATA = "av-engines"
AV_ENGINE_VERSION_METADATA = "av-versions"
AV_STATUS_METADATA = "av-status"
AV_MIME_METADATA = "av-mime"
AV_SQS_NAME = "av-sqs-name"
AV_STATUS_SNS_ARN = os.getenv("AV_STATUS_SNS_ARN")
AV_STATUS_SNS_PUBLISH_CLEAN = os.getenv("AV_STATUS_SNS_PUBLISH_CLEAN", "True")
AV_STATUS_SNS_PUBLISH_INFECTED = os.getenv("AV_STATUS_SNS_PUBLISH_INFECTED", "True")
AV_TIMESTAMP_METADATA = os.getenv("AV_TIMESTAMP_METADATA", "av-timestamp")
AV_UPDATE_METADATA = os.getenv("AV_UPDATE_METADATA", None)
AV_UPDATE_TAGS = os.getenv("AV_UPDATE_TAGS", 'False')
CLAMAVLIB_PATH = os.getenv("CLAMAVLIB_PATH", "./bin")
CLAMSCAN_PATH = os.getenv("CLAMSCAN_PATH", "./bin/clamscan")
FRESHCLAM_PATH = os.getenv("FRESHCLAM_PATH", "./bin/freshclam")
AV_PROCESS_ORIGINAL_VERSION_ONLY = os.getenv(
    "AV_PROCESS_ORIGINAL_VERSION_ONLY", "False"
)
AV_DELETE_INFECTED_FILES = os.getenv("AV_DELETE_INFECTED_FILES", "False")
SQS_URI = os.getenv("SQS_URI")
S3_URI = os.getenv("S3_URI")
SCANNER_LOCK = "/tmp/lock_scan"
# AWS_TLS_CA_BUNDLE = os.getenv("AWS_TLS_CA_BUNDLE", "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem")
AWS_TLS_CA_BUNDLE = os.getenv("AWS_TLS_CA_BUNDLE", None)
AWS_CERT_VERIFY = bool(strtobool(os.getenv("AWS_CERT_VERIFY", 'True')))
MVS_NOTIFY_SLACK = True
SLACK_NOTIFY = os.getenv("SLACK_NOTIFY")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
SLACK_USER = "mvs"
SLACK_ENDPOINT = os.getenv("SLACK_ENDPOINT")

LOG_DIR = '/var/log/multiav'
LOG_LEVEL_DEF = logging.INFO
KB = 1024
MB = 1024**2
GB = 1024**3

# Archive formats to unpack
ARCHIVES = ['.zip', '.tar', '.gz', '.tgz', '.gztar', '.bztar', '.cpio', '.jar', '.7z', '.bz2', '.rpm', '.lrz', '.lha', '.lz', '.lzma', '.lzo', '.lzh', '.ace', '.alz', '.rar', '.arc', '.rz', '.xz', '.xztar']

# AWS common
S3_MAX_POOL_CONNECTIONS = 100
S3_PREFIX = '/tmp/s3_scan'

INFECTED_BUCKET = os.getenv("INFECTED_BUCKET", "data-multiscan-infected")
UNSCANNED_BUCKET = os.getenv("UNSCANNED_BUCKET", "data-multiscan-unscanned")
INPUT_SQS_PATH = os.getenv("INPUT_SQS_PATH", "https://sqs.us-east-1.amazonaws.com/301802923513/multiscan-input-s3-events")
OUTPUT_SQS_PATH = os.getenv("OUTPUT_SQS_PATH", "https://sqs.us-east-1.amazonaws.com/301802923513/multiscan-output-s3-events")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

BATCHING_TIME = 10
BATCH_SIZE = os.getenv("BATCH_SIZE", 10)

def force_remove(func, path, exc_info):
    try:
        result = subprocess.run(
            ["sudo", "-n", "rm", "-rf", "--", path],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("sudo file delete failed for %s: %s", fs_object, e.stderr.strip())
        return False

def get_tmp_dir(path):
    try:
        dir_list = os.listdir(path)
        # make sure dir is empty
        # needed only during multiple restarts
        if len(dir_list) != 0:
            for files in dir_list:
                fs_object = os.path.join(path, files)
                try:
                    shutil.rmtree(fs_object, onerror=force_remove)
                except OSError:
                    os.remove(fs_object)
        tmpdir = tempfile.mkdtemp(dir=path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    return tmpdir


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(log_file):
    file_handler = TimedRotatingFileHandler(log_file, 'H', 4, 12)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name, level, log_file):
    log_file_name = get_log_file(log_file)
    logger_name = '[' + logger_name + ']'
    if logging.getLogger(logger_name).hasHandlers():
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(get_console_handler())
        logger.addHandler(get_file_handler(log_file_name))
        logger.propagate = False
    return logger


def get_log_file(log_file):
    try:
        instanceid = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id', timeout=1).read().decode()
    except Exception as e:
        print(f"Exception {e} -- occured while getting AWS instance id")
        instanceid = "00001"
    log_file_name = LOG_DIR + '/' + log_file + '-' + instanceid + '.log'
    return log_file_name


def create_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


def remove_empty_folders(path, removeRoot=False):
    for (_path, _dirs, _files) in os.walk(path, topdown=False):
        if _files:
            continue
        try:
            if os.path.samefile(str(path), str(_path)) and not removeRoot:
                continue
            os.rmdir(_path)
            # print('Remove :', _path)
        except OSError:
            continue


def list_files(src):
    file_list = []
    path = Path(src)
    for item in path.glob('**/*'):
        if os.path.isfile(item):
            file_list.append(item)
    return file_list


def get_timestamp():
    return datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S UTC")


class bcolors:
    HEADER = '\033[95m'
    DEBUG = '\033[94m'
    CYAN = '\033[96m'
    PASSING = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
