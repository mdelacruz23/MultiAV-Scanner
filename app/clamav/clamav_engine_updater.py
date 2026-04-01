#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import time

from aws_s3.common_defs import ENGINE_PREFIX
from aws_s3.common_defs import SCANNER_NAME
from aws_s3.common_defs import ENGINE_BUCKET
from aws_s3.common_defs import ENGINE_URI
from aws_s3.common_defs import ENGINE_ACCESS
from aws_s3.common_defs import ENGINE_SECRET
from aws_s3.common_defs import LOG_ENGINE_FILENAME
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import get_logger

from aws_s3.engine_updater import engine_updater

LOG_NAME = 'clamav_engine_updater'
global log_level
log_level = LOG_LEVEL_DEF


def main():
    parser = argparse.ArgumentParser(description="Clam AntiVirus: Engine Updater ")
    parser.add_argument("-a", "--accesskey", type=str, default=(ENGINE_ACCESS), help="Access Key")
    parser.add_argument("-s", "--secretkey", type=str, default=(ENGINE_SECRET), help="Secret Key")
    parser.add_argument("--uri", type=str, default=(ENGINE_URI), help="Minio Uri")
    required_named = parser.add_argument_group('required named arguments')
    required_named.add_argument("-b", "--bucket", type=str, default=(ENGINE_BUCKET), help="definitions S3 bucket")
    required_named.add_argument("-p", "--prefix", type=str, default=(ENGINE_PREFIX), help="engine directory in s3 bucket")
    required_named.add_argument("-c", "--checks",  type=int, default=1, help="number of engine update checks per day")
    required_named.add_argument("-d", "--download", dest='download', action='store_true', help="to download engine to/from s3 bucket")
    required_named.add_argument("-u", "--upload", dest='upload', action='store_true', help="upload engine to/from s3 bucket")
    args = parser.parse_args()
    bucket = args.bucket
    prefix = args.prefix
    download = args.download
    upload = args.upload
    uri = args.uri
    accesskey = args.accesskey
    secretkey = args.secretkey
    checks = args.checks
    # Validate arguments and
    if not bucket or not prefix:
        parser.error("clamav engine bucket and prefix must be provided")
    # check if Minio is being used
    if (accesskey and not secretkey) or (secretkey and not accesskey):
        parser.error('Both access key and secret key are required')
    if uri and not accesskey:
        parser.error('If uri is given tnen access key and secret key must be provided')
    if not download and not upload:
        parser.error('Either --download/-d or --upload/-u must be provided')
    target = ("download from ", "upload to ")[download]
    global log
    prefix = prefix + '/' + SCANNER_NAME
    log = get_logger(LOG_NAME, log_level, LOG_ENGINE_FILENAME)
    log.info(f'log_level: {log_level}')
    log.info(f"Checking for clamav engine updates to {target} s3 bucket: {bucket} prefix: {prefix}")
    while True:
        engine_updater(bucket, prefix, download, uri, accesskey, secretkey)
        deepsleep(checks)


def deepsleep(checks):
    interval = int(24 * 3600 / checks)
    log.info(f"Sleeping for {interval} seconds")
    for i in range(interval):
        time.sleep(1)


if __name__ == '__main__':
    main()
