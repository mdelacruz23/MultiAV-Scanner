#!/usr/bin/env python
import boto3
import botocore.exceptions
import datetime
import pytz
from datetime import timedelta
from functions.file_filter import get_s3_keys

s3 = boto3.resource('s3')
LOGS_BUCKET_NAME = 'data-dz-logs'
SEARCH_FILE_NAME = '/tmp/log_search'
search_bucket = s3.Bucket(LOGS_BUCKET_NAME)
MAX_COUNT = 300


def search_files(drop_bucket, key, z_log, range=1):
    # drop_bucket = key.split('/')[0]
    search_key = key.split('/')[-1]
    prov_info = "\nProvider: Unknown"
    utc = pytz.UTC

    time_now = datetime.datetime.now()
    time_now = time_now.replace(tzinfo=utc)
    # search window is set to 1 day
    # note that search can be very slow.
    day_range = int(range)
    prefix = {drop_bucket.strip()}
    start_search_time = time_now - timedelta(days=day_range)
    start_search_time = start_search_time.replace(tzinfo=utc)
    z_log.info(f"key: {key} search key: {search_key} search_bucket: {search_bucket} drop_bucket: {drop_bucket} prefix: {prefix} start date: {start_search_time}")
    counter = 0

    keys = get_s3_keys(LOGS_BUCKET_NAME, prefix, None, start_search_time, time_now)
    key_list = list(keys)
    key_list.sort(reverse=True)

    for file in key_list:
        if counter < MAX_COUNT:
            counter += 1
            try:
                if file.endswith('/'):
                    z_log.info(f"Skipping dir {file}")
                    continue
                z_log.debug(f"Matching file: {file} counter {counter}")
                s3.Bucket(LOGS_BUCKET_NAME).download_file(file, SEARCH_FILE_NAME)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    z_log.error(f"object {file} does not exist.")
                else:
                    z_log.warning(f"Failure to download object {file}")
                    return prov_info
            with open(SEARCH_FILE_NAME, 'r') as fp:
                for l_no, line in enumerate(fp):
                    # search for key
                    if search_key in line:
                        line_tokens = line.split()
                        AWS_Account = line_tokens[0]
                        drop_bucket = line_tokens[1]
                        drop_time = line_tokens[2].replace('[', ' ', 1)
                        IP_Address = line_tokens[4]
                        AWS_Login = line_tokens[5]
                        prov_info = f"\nDROP TIME: {drop_time} \nAWS ACCOUNT: {AWS_Account} \nAWS LOGIN: {AWS_Login} \n REMOTE IP: {IP_Address}"
                        return prov_info
                    else:
                        continue
        else:
            z_log.warning(f"Didn't find provider info for key: {key} search key: {search_key} search_bucket: {search_bucket} drop_bucket: {drop_bucket} prefix: {prefix} start date: {start_search_time}")
            break
    return prov_info
