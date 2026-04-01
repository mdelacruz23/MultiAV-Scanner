# -*- coding: utf-8 -*-
# A set of functions to download AV uvscan engine from S3

# import hashlib
import os
import os.path
# from pathlib import Path
from aws_s3.common_defs import UVSCAN_ENGINE_TMP_DIR
from aws_s3.common_defs import UVSCAN_ENGINE_DIR
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_FILENAME
from aws_s3.common_defs import sha256_from_file
from aws_s3.common_defs import sha256_from_s3_tags
from aws_s3.common_defs import get_logger

LOG_NAME = 'S3-engine-download'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)


def s3_engine_download(s3_client, bucket, prefix, engine_dir, engine_tmp_dir, defs_prefix_set, defs_suffix_set):

    os.makedirs(UVSCAN_ENGINE_TMP_DIR, exist_ok=True)
    os.makedirs(UVSCAN_ENGINE_DIR, exist_ok=True)
    to_download = {}
    local_file_sha256 = 0
    dat_keys = []
    for key in get_s3_keys(s3_client, bucket, prefix, defs_suffix_set):
        log.info(f"Adding file for download {key}")
        dat_keys.append(key)
    log.info(f"Uvscan key set: {dat_keys}")
    for key in dat_keys:
        filename = os.path.basename(key)
        local_file_path = os.path.join(engine_dir, filename)
        local_tmp_path = os.path.join(engine_tmp_dir, filename)
        log.info(f"local_file_path: {local_file_path} local_tmp_path: {local_tmp_path}")

        try:
            s3_sha256 = sha256_from_s3_tags(s3_client, bucket, key)
        except Exception as e:
            log.error(f"SHA256 failed bucket: {bucket} key: {key} due to: {e}")

        log.info(f"bucket: {bucket} key: {key} s3_sha256: {s3_sha256}")
        if os.path.exists(local_file_path):
            local_file_sha256 = sha256_from_file(local_file_path)
            log.info(f"local sha256: {local_file_sha256} s3_sha256: {s3_sha256}")
            if local_file_sha256 == s3_sha256:
                log.info(f"Not downloading {key} because local sha256 matches s3.")
                continue
        if s3_sha256:
            log.info(f"file: {key} local sha256: {local_file_sha256} s3 sha256: {s3_sha256}")
            to_download[filename] = {
                "s3_path": key,
                "local_tmp_path": local_tmp_path,
            }
    return to_download


def get_s3_keys(s3_client, bucket, prefix, suffix_set):
    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    log.debug(f"Request: bucket: {bucket} prefix: {prefix} suffix_set: {suffix_set}")
    while True:
        try:
            resp = s3_client.list_objects_v2(**kwargs)
            log.debug(f"resppnse from S3 list: {resp}")
        except Exception as e:
            log.error(f"list s3 objects from Bucket: {bucket} Prefix: {prefix} FAILED due to: {e}")
            break
        if 'Contents' in resp:
            for obj in resp['Contents']:
                key = obj['Key']
                if key.startswith(prefix) and key.endswith(suffix_set):
                    log.info(f"Found key: {key}")
                    yield key
            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break
        else:
            log.error(f"No key found in bucket : {bucket} prefix: {prefix} suffix_set: {suffix_set}")
            log.error("Check bucket and prefix name !!!")
            return None
