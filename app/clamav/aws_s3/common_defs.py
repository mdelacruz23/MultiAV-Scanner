# -*- coding: utf-8 -*-

import datetime
import os
import sys

import hashlib
import botocore
import logging
from logging.handlers import TimedRotatingFileHandler

FORMATTER = logging.Formatter('%(asctime)-15s - %(name)s - %(levelname)s - %(funcName)s -> %(message)s')

# EC2_INSTANCE = os.getenv("EC2_INSTANCE")
LOG_DIR = '/var/log/clamav'
LOG_FILENAME = "freshclam-local"
LOG_LEVEL_DEF = logging.INFO

LOG_ENGINE_FILENAME = 'clamav-engine'

DEFS_BUCKET = os.getenv("DEFS_BUCKET")
DEFS_URI = os.getenv("DEFS_URI")
DEFS_ACCESS = os.getenv("DEFS_ACCESS")
DEFS_SECRET = os.getenv("DEFS_SECRET")

ENGINE_BUCKET = DEFS_BUCKET
ENGINE_URI = DEFS_URI
ENGINE_ACCESS = DEFS_ACCESS
ENGINE_SECRET = DEFS_SECRET
FRESHCLAM_SRC_CONF = '/app/bin/freshclam.conf'
FRESHCLAM_DST_CONF = '/usr/local/etc/freshclam.conf'
CLAMD_SRC_CONF = '/app/clamav/clamd.conf'
CLAMD_DST_CONF = '/usr/local/etc/clamd.conf'
SCANNER_NAME = "clamav"

ENGINE_PREFIX = os.getenv("ENGINE_PREFIX", "scanners_engines")
clamav_engine_tmp_dir = "/tmp/" + ENGINE_PREFIX + "/" + SCANNER_NAME
CLAMAV_ENGINE_TMP_DIR = os.getenv("CLAMAV_ENGINE_PATH", clamav_engine_tmp_dir)
CLAMAV_ENGINE_DIR = "/var/opt/clamav_engine"

DEFS_PREFIX = os.getenv("DEFS_PREFIX", "scanners_defs")
tmp_dir = "/tmp/" + DEFS_PREFIX + "/" + SCANNER_NAME
CLAMAV_TMP_DIR = os.getenv("CLAMAV_DEFS_PATH", tmp_dir)
CLAMAV_LIB_DIR = "/var/lib/clamav"
CLAMAV_ENGINE_FILE_PREFIXES = "clamav"
CLAMAV_ENGINE_FILE_SUFFIXES = "deb"

CLAMAV_DEFS_FILE_PREFIXES = ["main", "daily", "bytecode"]
CLAMAV_DEFS_FILE_SUFFIXES = ["cld", "cvd", "cdb", "cfg", "crb", "fp", "ftm", "hdb", "hdu", "hsb", "hsu", "idb", "lgn", "lgn2", "info", "ldb", "ldu", "mdb", "mdu", "msb", "msu", "ndb", "ndu", "pdb", "sfp", "wdb"]


def get_timestamp():
    return datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S UTC")


def sha256_from_file(filename):
    hash_sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def sha256_from_s3_tags(s3_client, bucket, key):
    try:
        tags = s3_client.get_object_tagging(Bucket=bucket, Key=key)["TagSet"]
    except botocore.exceptions.ClientError as e:
        expected_errors = {"404", "AccessDenied", "NoSuchKey"}
        if e.response["Error"]["Code"] in expected_errors:
            return ""
        else:
            raise
    for tag in tags:
        if tag["Key"] == "sha256":
            return tag["Value"]

    raise Exception("SHA256 Tag not present in dat file")
    return ""


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
    log_file_name = LOG_DIR + '/' + log_file + '.log'
    return log_file_name
