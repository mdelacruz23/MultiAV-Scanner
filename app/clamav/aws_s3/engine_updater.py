# -*- coding: utf-8 -*-
import os
import os.path
import boto3
import shutil
import sys
import subprocess

from aws_s3.common_defs import CLAMAV_ENGINE_TMP_DIR
from aws_s3.common_defs import CLAMAV_ENGINE_DIR
from aws_s3.common_defs import CLAMAV_ENGINE_FILE_PREFIXES
from aws_s3.common_defs import CLAMAV_ENGINE_FILE_SUFFIXES
from aws_s3.common_defs import FRESHCLAM_SRC_CONF
from aws_s3.common_defs import FRESHCLAM_DST_CONF
from aws_s3.common_defs import CLAMD_SRC_CONF
from aws_s3.common_defs import CLAMD_DST_CONF

from aws_s3.s3_engine_download import s3_engine_download
from aws_s3.s3_engine_upload import s3_engine_upload
from aws_s3.common_defs import SCANNER_NAME
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_ENGINE_FILENAME
from aws_s3.common_defs import get_logger

LOG_NAME = 'engine-updater'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_ENGINE_FILENAME)


def engine_updater(bucket, prefix, download, uri, accesskey, secretkey):
    if uri:
        # the endpoint override has been provided set the endpoint.
        # (per Amazon docs this should only be configured at client creation)
        s3 = boto3.resource('s3', endpoint_url=uri, verify=False,
                            aws_access_key_id=accesskey,
                            aws_secret_access_key=secretkey)
        s3_client = boto3.client('s3', endpoint_url=uri, verify=False,
                                 aws_access_key_id=accesskey,
                                 aws_secret_access_key=secretkey)
    else:
        s3 = boto3.resource("s3")
        s3_client = boto3.client("s3")

    new_version = False
    if download:
        log.info(f"Downloading new engine version. Bucket: {bucket} Prefix: {prefix}")
        new_version = download_engine(s3_client, s3, bucket, prefix)
        if new_version:
            # Move files to engine dir
            engine_files = os.listdir(CLAMAV_ENGINE_TMP_DIR)
            if not os.path.exists(CLAMAV_ENGINE_DIR):
                os.mkdir(CLAMAV_ENGINE_DIR)
            try:
                for file in engine_files:
                    engine_package = os.path.join(CLAMAV_ENGINE_DIR, file)
                    shutil.move(os.path.join(CLAMAV_ENGINE_TMP_DIR, file),
                                engine_package)
                    # os.path.join(CLAMAV_ENGINE_DIR, file))
                    # install the new engine
                    log.info(f"Installing the new engine {file}")
                    subprocess.check_call([f"/usr/bin/sudo /usr/bin/dpkg -i {engine_package}"], shell=True)
                    shutil.copyfile(CLAMD_SRC_CONF, CLAMD_DST_CONF)
                    shutil.copyfile(FRESHCLAM_SRC_CONF, FRESHCLAM_DST_CONF)
                    log.info(f"{SCANNER_NAME} new engine {file} installed successfully")
            except Exception as e:
                log.error(f"Failed to install {SCANNER_NAME}  new engine {file} due to: {e}")
    else:
        log.info(f"Uploading engine. Bucket: {bucket} Prefix: {prefix}")
        new_version = s3_engine_upload(s3_client, s3, bucket, prefix, CLAMAV_ENGINE_TMP_DIR)
    return new_version


def download_engine(s3_client, s3, bucket, prefix):

    log.info("starting download of engine from s3")
    # check if engine as been updated
    to_download = s3_engine_download(
        s3_client, bucket, prefix, CLAMAV_ENGINE_DIR, CLAMAV_ENGINE_TMP_DIR,
        CLAMAV_ENGINE_FILE_PREFIXES, CLAMAV_ENGINE_FILE_SUFFIXES)
    # download engine if it's a new version
    updated = False
    for download in to_download.values():
        s3_path = download["s3_path"]
        local_tmp_path = download["local_tmp_path"]
        log.info(f"Downloading engine file {os.path.basename(s3_path)} from s3://{bucket}/{s3_path}")
        try:
            s3.Bucket(bucket).download_file(s3_path, local_tmp_path)
        except Exception as e:
            log.error(f"Download engine file {os.path.basename(s3_path)}  FAILED due to: {e}")
        updated = True
        log.info(f"Download engine file {os.path.basename(s3_path)}  completed!")
    log.info("finished downloading engine from s3")
    return updated
