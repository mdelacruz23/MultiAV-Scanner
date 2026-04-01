# -*- coding: utf-8 -*-
import os
import os.path
import boto3
import shutil
# import subprocess

from aws_s3.common_defs import UVSCAN_ENGINE_TMP_DIR
from aws_s3.common_defs import UVSCAN_ENGINE_DIR
from aws_s3.common_defs import UVSCAN_INSTALL_DIR
from aws_s3.common_defs import UVSCAN_ENGINE_FILE_PREFIXES
from aws_s3.common_defs import UVSCAN_ENGINE_FILE_SUFFIXES
from aws_s3.s3_engine_download import s3_engine_download
from aws_s3.s3_engine_upload import s3_engine_upload
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_FILENAME

from aws_s3.common_defs import get_logger
# from distutils.errors import DistutilsExecError
LOG_NAME = 'engine-updater'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)


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
        new_version = download_engines(s3_client, s3, bucket, prefix)
        if new_version:

            # attempt to unpack, validate, install
            # try:
            #     env = dict(os.environ)
            #     cmd = "/app/uvscan/local_updater.sh"
            #     proc = subprocess.Popen(cmd, env=env)
            #     proc.wait()
            #     exitcode = proc.returncode
            # except OSError as exc:
            #     cmd = cmd[0]
            #     raise DistutilsExecError(
            #         "command %r failed: %s" % (cmd, exc)) from exc

            # if exitcode:
            #     cmd = cmd[0]
            #     raise DistutilsExecError(
            #           "command %r failed with exit code %s" % (cmd, exitcode))

            # Move files to uvscan dir
            engine_files = os.listdir(UVSCAN_ENGINE_TMP_DIR)
            for engine in engine_files:
                shutil.move(os.path.join(UVSCAN_ENGINE_TMP_DIR, engine),
                            os.path.join(UVSCAN_ENGINE_DIR, engine))

            # needs to be done after verification
            for engine in engine_files:
                shutil.copyfile(os.path.join(UVSCAN_ENGINE_DIR, engine),
                            os.path.join(UVSCAN_INSTALL_DIR, engine))
                os.chmod(os.path.join(UVSCAN_INSTALL_DIR, engine), 0o755)
    else:
        log.info(f"Uploading new engine version. Bucket: {bucket} Prefix: {prefix}")
        new_version = s3_engine_upload(s3_client, s3, bucket, prefix, UVSCAN_ENGINE_TMP_DIR)
    return new_version


def download_engines(s3_client, s3, bucket, prefix):

    log.info("starting update uvscan engine from s3")
    to_download = s3_engine_download(
        s3_client, bucket, prefix, UVSCAN_ENGINE_DIR,
        UVSCAN_ENGINE_TMP_DIR, UVSCAN_ENGINE_FILE_PREFIXES, UVSCAN_ENGINE_FILE_SUFFIXES
    )
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
    return updated
