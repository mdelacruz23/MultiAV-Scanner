# -*- coding: utf-8 -*-
import os
import os.path
import boto3
import shutil
import clamd

from aws_s3.common_defs import CLAMAV_TMP_DIR
from aws_s3.common_defs import CLAMAV_LIB_DIR
from aws_s3.common_defs import CLAMAV_DEFS_FILE_PREFIXES
from aws_s3.common_defs import CLAMAV_DEFS_FILE_SUFFIXES
from aws_s3.s3_download import s3_download
from aws_s3.s3_upload import s3_upload
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_FILENAME

from aws_s3.common_defs import get_logger

LOG_NAME = 'defs-updater'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)


def clamav_defs_updater(bucket, prefix, download, uri, accesskey, secretkey):
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
        log.info(f"Downloading virus definitions. Bucket: {bucket} Prefix: {prefix}")
        new_version = download_defs(s3_client, s3, bucket, prefix)
        if new_version:
            # Move files to clamav dir and notify clamd to reload db
            nDatabases = os.listdir(CLAMAV_TMP_DIR)
            for database in nDatabases:
                shutil.move(os.path.join(CLAMAV_TMP_DIR, database),
                            os.path.join(CLAMAV_LIB_DIR, database))
            try:
                log.info("sending RELOAD notification to clamd")
                cd = clamd.ClamdUnixSocket()
                cd.reload()
            except Exception as e:
                log.error(f"Failed to notify clamd due to: {e}")
    else:
        log.info(f"Uploading virus definitions. Bucket: {bucket} Prefix: {prefix}")
        new_version = s3_upload(s3_client, s3, bucket, prefix, CLAMAV_TMP_DIR)
    return new_version


def download_defs(s3_client, s3, bucket, prefix):

    log.info("starting update clamav virus definitions from s3")
    # check which definitions were updated
    to_download = s3_download(
        s3_client, bucket, prefix, CLAMAV_LIB_DIR,
        CLAMAV_TMP_DIR, CLAMAV_DEFS_FILE_PREFIXES, CLAMAV_DEFS_FILE_SUFFIXES
    )
    # download definitions that were updated
    updated = False
    for download in to_download.values():
        s3_path = download["s3_path"]
        local_tmp_path = download["local_tmp_path"]
        log.info(f"Downloading definition file {os.path.basename(s3_path)} from s3://{bucket}/{s3_path}")
        try:
            s3.Bucket(bucket).download_file(s3_path, local_tmp_path)
        except Exception as e:
            log.error(f"Download definition file {os.path.basename(s3_path)}  FAILED due to: {e}")
        updated = True
        log.info(f"Download definition file {os.path.basename(s3_path)}  completed!")
    log.info("finished updating clamav virus definitions from s3")
    return updated
