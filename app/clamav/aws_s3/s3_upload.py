import os
from aws_s3.common_defs import CLAMAV_DEFS_FILE_PREFIXES
from aws_s3.common_defs import CLAMAV_DEFS_FILE_SUFFIXES
from aws_s3.common_defs import sha256_from_file
from aws_s3.common_defs import sha256_from_s3_tags
from aws_s3.common_defs import get_timestamp
from aws_s3.common_defs import LOG_LEVEL_DEF
from aws_s3.common_defs import LOG_FILENAME

from aws_s3.common_defs import get_logger

LOG_NAME = 'S3-upload'

global log_level
log_level = LOG_LEVEL_DEF
global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)


# This function is to be used for testing only!


def s3_upload(s3_client, s3, bucket, prefix, local_path):
    for file_prefix in CLAMAV_DEFS_FILE_PREFIXES:
        for file_suffix in CLAMAV_DEFS_FILE_SUFFIXES:
            filename = file_prefix + "." + file_suffix
            local_file_path = os.path.join(local_path, filename)
            if os.path.exists(local_file_path):
                local_file_sha256 = sha256_from_file(local_file_path)
                s3_file_sha256 = sha256_from_s3_tags(s3_client, bucket, os.path.join(prefix, filename))
                if (local_file_sha256 != s3_file_sha256):
                    log.info(f"file: {filename} local sha256: {local_file_sha256} s3 sha256: {s3_file_sha256}")
                    log.info(f"Uploading {local_file_path} to s3://{os.path.join(bucket, prefix, filename)}")
                    try:
                        s3_object = s3.Object(bucket, os.path.join(prefix, filename))
                        s3_object.upload_file(os.path.join(local_path, filename))
                        s3_client.put_object_tagging(
                            Bucket=s3_object.bucket_name,
                            Key=s3_object.key,
                            Tagging={"TagSet": [{"Key": "sha256", "Value": local_file_sha256}]},
                        )
                        log.info(f"Upload clamav virus definitions file {filename} \
                              to s3 bucket: {bucket} Key: {prefix} completed at {get_timestamp()}")
                    except Exception as e:
                        log.error(f"Upload definition file {filename} to s3 bucket: {s3_object.bucket_name} Key: {s3_object.key}  FAILED due to: {e}")

                else:
                    log.info(f"Not uploading {filename} because sha256 on remote matches local.")
            else:
                log.info(f"File does not exist: {local_file_path}")
