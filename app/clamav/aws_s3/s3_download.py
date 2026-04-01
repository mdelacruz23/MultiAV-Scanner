# -*- coding: utf-8 -*-
# A set of functions to download clamav files from S3

# import hashlib
import os
from pathlib import Path
from aws_s3.common_defs import sha256_from_file
from aws_s3.common_defs import sha256_from_s3_tags
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_FILENAME
from aws_s3.common_defs import get_logger

LOG_NAME = 'S3-download'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)


def s3_download(s3_client, bucket, prefix, lib_path, tmp_defs_path, defs_prefix_set, defs_suffix_set):

    Path(tmp_defs_path).mkdir(parents=True, exist_ok=True)
    to_download = {}
    local_file_sha256 = 0
    for file_prefix in defs_prefix_set:
        for file_suffix in defs_suffix_set:
            filename = file_prefix + "." + file_suffix
            key = os.path.join(prefix, filename)
            local_lib_path = os.path.join(lib_path, filename)
            local_tmp_path = os.path.join(tmp_defs_path, filename)
            try:
                s3_sha256 = sha256_from_s3_tags(s3_client, bucket, key)
            except Exception as e:
                log.error(f"SHA256 failed bucket: {bucket} key: {key} due to: {e}")

            log.info(f"bucket: {bucket} key: {key} s3_sha256: {s3_sha256}")
            if os.path.exists(local_lib_path):
                local_file_sha256 = sha256_from_file(local_lib_path)
                if local_file_sha256 == s3_sha256:
                    log.info(f"Not downloading {filename} because local sha256 matches s3.")
                    continue
            if s3_sha256:
                log.info(f"file: {filename} local sha256: {local_file_sha256} s3 sha256: {s3_sha256}")
                to_download[filename] = {
                    "s3_path": key,
                    "local_tmp_path": local_tmp_path,
                }
    return to_download
