import argparse
import boto3
import dateutil.parser
import logging
import pytz
from collections import namedtuple

logger = logging.getLogger(__name__)


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


def valid_datetime(date):
    if date is None:
        return date
    try:
        utc = pytz.UTC
        return utc.localize(dateutil.parser.parse(date))
    except Exception:
        raise argparse.ArgumentTypeError("Could not parse value: '{}' to type datetime".format(date))


def main():
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description='List keys in S3 bucket for prefix')
    parser.add_argument('-b', '--bucket', help='S3 Bucket')
    parser.add_argument('-p', '--prefixes', nargs='+', help='Filter s3 keys by a set of prefixes')
    parser.add_argument('-s', '--suffixes', nargs='*', help='Filter s3 keys by a set of suffixes')
    parser.add_argument('-n', '--last_modified_min', default=None, type=valid_datetime, help='Filter s3 content by minimum last modified date')
    parser.add_argument('-x', '--last_modified_max', default=None, type=valid_datetime, help='Filter s3 content by maximum last modified date')
    parser.add_argument('-o', '--object', help='s3 object to seach for')
    parser.add_argument('-f', '--file', help='Optional: file to write keys to.', default=None)

    args = parser.parse_args()
    logger.info(args)
    keys = get_s3_keys(args.bucket, args.prefixes, args.suffixes, args.last_modified_min, args.last_modified_max)
    open_file = open(args.file, 'w') if args.file else None
    try:
        counter = 0
        for key in keys:
            print(key, file=open_file)
            counter += 1
    finally:
        if open_file is not None:
            open_file.close()

    logger.info('Retrieved {} keys'.format(counter))


if __name__ == '__main__':
    main()
