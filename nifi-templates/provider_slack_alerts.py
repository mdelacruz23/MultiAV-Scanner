#!/usr/bin/env python
import boto3
import botocore.exceptions
import datetime
from datetime import timedelta
import sys
import pytz
from collections import namedtuple

s3 = boto3.resource('s3')
LOGS_BUCKET_NAME = 'data-dz-logs'
SEARCH_FILE_NAME = '/tmp/log_search'
search_bucket = s3.Bucket(LOGS_BUCKET_NAME)
MAX_COUNT = 300


Rule = namedtuple('Rule', ['has_min', 'has_max'])
last_modified_rules = {
    Rule(has_min=True, has_max=True):
        lambda min_date, date, max_date: min_date <= date <= max_date,
    Rule(has_min=True, has_max=False):
        lambda min_date, date, max_date: min_date <= date,
    Rule(has_min=False, has_max=True):
        lambda min_date, date, max_date: date <= max_date,
    Rule(has_min=False, has_max=False):
        lambda min_date, date, max_date: True,
}


def get_s3_objects(bucket, prefixes=None, suffixes=None, last_modified_min=None, last_modified_max=None):
    """
    Generate the objects in an S3 bucket. Adapted from:
    https://alexwlchan.net/2017/07/listing-s3-keys/

    :param bucket: Name of the S3 bucket.
    :ptype bucket: str
    :param prefixes: Only fetch keys that start with these prefixes (optional).
    :ptype prefixes: tuple
    :param suffixes: Only fetch keys that end with thes suffixes (optional).
    :ptype suffixes: tuple
    :param last_modified_min: Only yield objects with LastModified dates greater than this value (optional).
    :ptype last_modified_min: datetime.date
    :param last_modified_max: Only yield objects with LastModified dates greater than this value (optional).
    :ptype last_modified_max: datetime.date

    :returns: generator of dictionary objects
    :rtype: dict https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.list_objects
    """
    if last_modified_min and last_modified_max and last_modified_max < last_modified_min:
        raise ValueError(
            "When using both, last_modified_max: {} must be greater than last_modified_min: {}".format(
                last_modified_max, last_modified_min
            )
        )
    # Use the last_modified_rules dict to lookup which conditional logic to apply
    # based on which arguments were supplied
    last_modified_rule = last_modified_rules[bool(last_modified_min), bool(last_modified_max)]

    if not prefixes:
        prefixes = ('',)
    else:
        prefixes = tuple(set(prefixes))
    if not suffixes:
        suffixes = ('',)
    else:
        suffixes = tuple(set(suffixes))

    s3 = boto3.client('s3')
    kwargs = {'Bucket': bucket}

    for prefix in prefixes:
        kwargs['Prefix'] = prefix
        while True:
            # The S3 API response is a large blob of metadata.
            # 'Contents' contains information about the listed objects.
            resp = s3.list_objects_v2(**kwargs)
            for content in resp.get('Contents', []):
                last_modified_date = content['LastModified']
                if (
                    content['Key'].endswith(suffixes) and
                    last_modified_rule(last_modified_min, last_modified_date, last_modified_max)
                ):
                    yield content

            # The S3 API is paginated, returning up to 1000 keys at a time.
            # Pass the continuation token into the next response, until we
            # reach the final page (when this field is missing).
            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break


def get_s3_keys(bucket, prefixes=None, suffixes=None, last_modified_min=None, last_modified_max=None):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :ptype bucket: str
    :param prefixes: Only fetch keys that start with these prefixes (optional).
    :ptype prefixes: tuple
    :param suffixes: Only fetch keys that end with thes suffixes (optional).
    :ptype suffixes: tuple
    :param last_modified_min: Only yield objects with LastModified dates greater than this value (optional).
    :ptype last_modified_min: datetime.date
    :param last_modified_max: Only yield objects with LastModified dates greater than this value (optional).
    :ptype last_modified_max: datetime.date
    """
    for obj in get_s3_objects(bucket, prefixes, suffixes, last_modified_min, last_modified_max):
        yield obj['Key']


def search_files(key, range=1):
    drop_bucket = key.split('/')[0]
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
    counter = 0

    keys = get_s3_keys(LOGS_BUCKET_NAME, prefix, None, start_search_time, time_now)
    key_list = list(keys)
    key_list.sort(reverse=True)

    for file in key_list:
        if counter < MAX_COUNT:
            counter += 1
            try:
                if file.endswith('/'):
                    continue
                s3.Bucket(LOGS_BUCKET_NAME).download_file(file, SEARCH_FILE_NAME)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    continue
                else:
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
            break
    return prov_info


def main(argv):
    key = argv[0]
    if len(sys.argv) > 2:
        range = argv[1]
    else:
        range = 1
    search_files(key, range)


if __name__ == "__main__":
    main(sys.argv[1:])
