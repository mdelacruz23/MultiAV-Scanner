import copy
import json
import os
import urllib
from distutils.util import strtobool
import os.path
from os import path
import pathlib
import re
import unicodedata

from botocore.exceptions import ClientError, ParamValidationError
from functions.common import AV_SCAN_START_METADATA
from functions.common import AV_SIGNATURE_METADATA
from functions.common import AV_ENGINE_METADATA
from functions.common import AV_ENGINE_VERSION_METADATA
from functions.common import AV_MIME_METADATA
from functions.common import AV_SQS_NAME
from functions.common import AV_STATUS_CLEAN
from functions.common import AV_STATUS_INFECTED
from functions.common import AV_STATUS_ERROR
from functions.common import AV_STATUS_METADATA
from functions.common import AV_STATUS_SNS_PUBLISH_CLEAN
from functions.common import AV_STATUS_SNS_PUBLISH_INFECTED
from functions.common import AV_TIMESTAMP_METADATA
from functions.common import INFECTED_BUCKET
from functions.common import UNSCANNED_BUCKET
from functions import metrics
from functions.common import bcolors
from functions.common import LOG_LEVEL_DEF
from functions.common import ARCHIVES
from functions.common import get_logger
from functions.slack_notify import slack_notify
from functions.common import SLACK_NOTIFY
from functions.common import GB

from functions.common import get_timestamp

LOG_FILENAME = 'S3multiav_scan'
LOG_NAME = 'S3Scanner-W'

# Logging levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
# Default logging level
LOG_LEVEL = os.getenv('LOGGING_LEVEL', LOG_LEVEL_DEF)
SAFE_TAG_RE = re.compile(r"[^A-Za-z0-9+\-=\._:/ @]")

global log_level

if LOG_LEVEL in LOG_LEVELS:
    log_level = LOG_LEVEL
else:
    log_level = LOG_LEVEL_DEF

print(f"Log level: {LOG_LEVEL_DEF}")

global log
log = get_logger(LOG_NAME, log_level, LOG_FILENAME)

def sanitize_s3_tag_value(value: str, max_len: int = 256) -> str:
    if value is None:
        return "UNKNOWN"

    # normalize unicode
    value = unicodedata.normalize("NFKD", str(value))

    # replace invalid chars with underscore
    value = SAFE_TAG_RE.sub("_", value)

    # collapse repeated underscores/spaces
    value = re.sub(r"_+", "_", value).strip(" _")

    if not value:
        value = "UNKNOWN"

    return value[:max_len]

def event_object(event, s3_resource, event_source="s3"):

    # Break down the record
    event = json.loads(event)
    log.debug(f"event: {event}")
    if 'Records' not in event:
        log.error(f"event_object: {event}")
        raise ValueError("No Records in event object")

    records = event['Records']
    if len(records) == 0:
        raise Exception("No records found in event!")
    record = records[0]

    s3_obj = record["s3"]

    # Get the bucket name
    if "bucket" not in s3_obj:
        raise Exception("No bucket found in event!")
    bucket_name = s3_obj["bucket"].get("name", None)

    # Get the key name
    if "object" not in s3_obj:
        raise Exception("No key found in event!")
    # key_name = s3_obj["object"].get("key", None)
    key_name = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    size = event['Records'][0]['s3']['object']['size']
    # Below quote_plus needs to be enabled for high-side but not on low-side?
    # if key_name:
    #    key_name = urllib.parse.quote_plus(key_name.encode("utf8"))

    # Ensure both bucket and key exist
    if (not bucket_name) or (not key_name):
        raise Exception("Unable to retrieve object from event.\n{}".format(event))

    # Create and return the object
    return s3_resource.Object(bucket_name, key_name), int(size)


def verify_s3_object_version(s3, s3_object):
    # validate that we only process the original version of a file, if asked to do so
    # security check to disallow processing of a new (possibly infected) object version
    # while a clean initial version is getting processed
    # downstream services may consume latest version by mistake and get the infected version instead
    bucket_versioning = s3.BucketVersioning(s3_object.bucket_name)
    if bucket_versioning.status == "Enabled":
        bucket = s3.Bucket(s3_object.bucket_name)
        versions = list(bucket.object_versions.filter(Prefix=s3_object.key))
        if len(versions) > 1:
            raise Exception(
                "Detected multiple object versions in %s.%s, aborting processing"
                % (s3_object.bucket_name, s3_object.key)
            )
    else:
        # misconfigured bucket, left with no or suspended versioning
        raise Exception(
            "Object versioning is not enabled in bucket %s" % s3_object.bucket_name
        )


def get_local_path(s3_object, prefix):
    z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
    z_log.debug(f"{bcolors.DEBUG}prefix: {prefix}  bucket_name: {s3_object.bucket_name} key: {s3_object.key} {bcolors.ENDC}")
    return os.path.join(prefix, s3_object.bucket_name, s3_object.key)


def delete_s3_object(s3_object):
    try:
        s3_object.delete()
    except Exception:
        raise Exception(
            "Failed to delete infected file: %s.%s"
            % (s3_object.bucket_name, s3_object.key)
        )
    else:
        z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
        z_log.warning(f"Infected file deleted: {s3_object.bucket_name} key: {s3_object.key}")


def set_av_metadata(s3_object, scan_result, signature, timestamp, scan_engine, scan_engine_version, mime_type):
    content_type = s3_object.content_type
    metadata = s3_object.metadata
    engine_versions = ""
    for key, value in scan_engine_version.items():
        # z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
        # z_log.debug(f"engine: {key} version: {value}")
        if engine_versions == "":
            engine_versions += value
        else:
            engine_versions = " :: ".join([engine_versions, value])
    # z_log.debug(f"set object metadata engine_versions: {engine_versions}")
    metadata[AV_SIGNATURE_METADATA] = signature
    metadata[AV_STATUS_METADATA] = scan_result
    metadata[AV_ENGINE_METADATA] = scan_engine
    metadata[AV_ENGINE_VERSION_METADATA] = engine_versions
    metadata[AV_MIME_METADATA] = mime_type
    metadata[AV_TIMESTAMP_METADATA] = timestamp
    s3_object.copy(
        {"Bucket": s3_object.bucket_name, "Key": s3_object.key},
        ExtraArgs={
            "ContentType": content_type,
            "Metadata": metadata,
            "MetadataDirective": "REPLACE",
        },
    )

def dedupe_tagset(tagset):
    d = {}
    for t in tagset:
        d[t["Key"]] = t["Value"]   # later entries overwrite earlier ones
    return [{"Key": k, "Value": v} for k, v in d.items()]

def set_av_tags(s3_client, s3_object, scan_result, signature, timestamp, scan_engine, scan_engine_version, mime_type, input_queue):
    z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)

    # curr_tags = s3_client.get_object_tagging(
   #     Bucket=s3_object.bucket_name, Key=s3_object.key
   # )["TagSet"]
    try:
        curr_tags = s3_client.get_object_tagging(
            Bucket=s3_object.bucket_name, Key=s3_object.key
        )["TagSet"]
    except s3_client.exceptions.NoSuchKey:
        z_log.warning(f"Object not found: s3://{s3_object.bucket_name}/{s3_object.key} — skipping tagging.")
        return
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            z_log.warning(f"Object missing: s3://{s3_object.bucket_name}/{s3_object.key} — skipping tagging.")
            return
        elif error_code == "MethodNotAllowed":
            z_log.warning(f"Tagging not allowed on object: s3://{s3_object.bucket_name}/{s3_object.key} — skipping tagging.")
            return
        else:
            raise
    new_tags = copy.copy(curr_tags)
    for tag in curr_tags:
        if not tag["Key"].endswith("-version") and tag["Key"] not in [
            AV_ENGINE_METADATA,
         #   AV_ENGINE_VERSION_METADATA,
            AV_SIGNATURE_METADATA,
            AV_STATUS_METADATA,
            AV_TIMESTAMP_METADATA,
            AV_MIME_METADATA,
            AV_SQS_NAME,
        ]:
            new_tags.append(tag)
    engine_versions = ""
    for key, value in scan_engine_version.items():
        if "Clam" in value:
            new_tags.append({"Key": "clamav-version", "Value": value})
        elif "McAfee" in value:
            new_tags.append({"Key": "mcafee-version", "Value": value})
        elif "Sophos" in value:
            new_tags.append({"Key": "sophos-version", "Value": value})

        if engine_versions == "":
            engine_versions += value
        else:
            engine_versions = " :: ".join([engine_versions, value])
    new_tags.append({"Key": AV_ENGINE_METADATA, "Value": scan_engine})
   # new_tags.append({"Key": AV_ENGINE_VERSION_METADATA, "Value": engine_versions})
    new_tags.append({"Key": AV_SIGNATURE_METADATA, "Value": sanitize_s3_tag_value(signature, 256)})
    new_tags.append({"Key": AV_STATUS_METADATA, "Value": scan_result})
    new_tags.append({"Key": AV_TIMESTAMP_METADATA, "Value": timestamp})
    new_tags.append({"Key": AV_MIME_METADATA, "Value": mime_type})
    new_tags.append({"Key": AV_SQS_NAME, "Value": input_queue})
    z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
    z_log.info(f"Bucket: {s3_object.bucket_name} Key: {s3_object.key} TAGS: engines: {scan_engine} signatures: {signature} engine_versions: {engine_versions} timestamp: {timestamp} mime_type: {mime_type} input_queue: {input_queue} scan_result: {scan_result}")
    try:
        new_tags = dedupe_tagset(new_tags)
        s3_client.put_object_tagging(
            Bucket=s3_object.bucket_name, Key=s3_object.key, Tagging={"TagSet": new_tags}
        )
    except Exception as e:
        z_log.error(f"tagging failed. bucket: {s3_object.bucket_name}, key: {s3_object.key} Reason: {e}")



def sns_start_scan(sns_client, s3_object, scan_start_sns_arn, timestamp):
    message = {
        "bucket": s3_object.bucket_name,
        "key": s3_object.key,
        "version": s3_object.version_id,
        AV_SCAN_START_METADATA: True,
        AV_TIMESTAMP_METADATA: timestamp,
    }
    sns_client.publish(
        TargetArn=scan_start_sns_arn,
        Message=json.dumps({"default": json.dumps(message)}),
        MessageStructure="json",
    )


def sns_scan_results(sns_client, s3_object, sns_arn, scan_result, signature):
    # Don't publish if scan_result is CLEAN and CLEAN results should not be published
    if scan_result == AV_STATUS_CLEAN and not str_to_bool(AV_STATUS_SNS_PUBLISH_CLEAN):
        return
    # Don't publish if scan_result is INFECTED and INFECTED results should not be published
    if scan_result == AV_STATUS_INFECTED and not str_to_bool(
        AV_STATUS_SNS_PUBLISH_INFECTED
    ):
        return
    message = {
        "bucket": s3_object.bucket_name,
        "key": s3_object.key,
        "version": s3_object.version_id,
        AV_SIGNATURE_METADATA: signature,
        AV_STATUS_METADATA: scan_result,
        AV_TIMESTAMP_METADATA: get_timestamp(),
    }
    sns_client.publish(
        TargetArn=sns_arn,
        Message=json.dumps({"default": json.dumps(message)}),
        MessageStructure="json",
        MessageAttributes={
            AV_STATUS_METADATA: {"DataType": "String", "StringValue": scan_result},
            AV_SIGNATURE_METADATA: {
                "DataType": "String",
                "StringValue": signature,
            },
        },
    )


def move_to_s3_bucket(s3_resource, s3_client, s3_object, bucket):
    try:
        lookup = s3_resource.meta.client.head_bucket(Bucket=bucket)
    except ClientError:
        lookup = None
    if lookup is not None:
        source_bucket = s3_object.bucket_name
        destination_bucket = bucket
        key = s3_object.key
        destination_path = "%s/%s" % (source_bucket, key)
        z_log = get_logger(source_bucket, log_level, source_bucket)
        z_log.info(f"{bcolors.DEBUG}Source: bucket: {source_bucket} key: {key} {bcolors.ENDC}")
        z_log.info(f"{bcolors.DEBUG}Destination: bucket: {destination_bucket} path: {destination_path} {bcolors.ENDC}")
        try:
            copy_source = {'Bucket': source_bucket, 'Key': key}
            z_log.debug(f"{bcolors.DEBUG}Item: {copy_source} {bcolors.ENDC}")
            s3_client.copy_object(CopySource=copy_source, Bucket=destination_bucket, Key=destination_path)
            s3_resource.Object(source_bucket, key).delete()
        except Exception as e:
            z_log.error(f"{bcolors.FAIL}Exception occured when copying object from: Source bucket: {source_bucket}  Key: {key} to: bucket: {destination_bucket}  path: {destination_path}  Exception: {e} {bcolors.ENDC}")
    else:
        z_log.error(f"{bcolors.FAIL}Error Bucket does not exist! {bcolors.ENDC}")
    return


def list_files(path):
    log.debug(f"{bcolors.DEBUG}files in {path} {bcolors.ENDC}")
    for root, dirs, files in os.walk(path):
        for filename in files:
            log.debug(f"{bcolors.DEBUG}filename: {filename} {bcolors.ENDC}")


def scan_handler(downloads, prefix, cpu_config, sqs, s3_resource, s3_client, input_sqs_queue, output_sqs_queue,  multi_av, speed, sequential):
    ENV = os.getenv("ENV", "")
    ret = multi_av.single_scan(prefix, speed) if sequential else multi_av.scan(prefix, speed)
    av_engine_versions = multi_av.versions()
    log.debug(f"scan returned: Versions: {av_engine_versions} Results: {ret}")
    for i in range(len(downloads)):
        if downloads[i] == 1 or downloads[i] is None:
            return
        file_path, message, EVENT_SOURCE, mime_type = downloads[i]
        event = message['Body']
        s3_object, object_size = event_object(event, s3_resource, event_source=EVENT_SOURCE)
        z_log = get_logger(s3_object.bucket_name, log_level, s3_object.bucket_name)
        object_size_gb = round((object_size / GB), 2)
        if SLACK_NOTIFY and object_size_gb >= 2:
            try:
                slack_notify(s3_object, object_size_gb, mime_type, input_sqs_queue, z_log)
            except Exception as e:
                z_log.error(f"{bcolors.FAIL} slack_notify failure {e}")
        try:
            z_log.debug(f"{bcolors.DEBUG}Scan results: {ret} {bcolors.ENDC}")
            scan_signature = []
            scan_result = AV_STATUS_CLEAN
            for scan_engine in ret:
                results = ret[scan_engine]
                suffix = pathlib.Path(file_path).suffix
                archive_dir = file_path
                if suffix is not None and any(x in suffix for x in ARCHIVES):
                    while any(x in suffix for x in ARCHIVES):
                        archive_dir = str(archive_dir).removesuffix(suffix)
                        log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} file_path: {file_path}{bcolors.ENDC}")
                        suffix = pathlib.Path(archive_dir).suffix

                    log.debug(f"{bcolors.DEBUG} archive_dir: {archive_dir} RESULTS: {results}{bcolors.ENDC}")
                    # for key, val in results.items():
                    #     log.info(f"key: {key} val: {val}")
                    sigs = [val for key, val in results.items() if str(archive_dir) in key]
        #            sigs = [val for key, val in results.items() if str(archive_dir).startswith(str(key))]
                    log.debug(f"{bcolors.DEBUG} sigs {sigs} type: {type(sigs)} {bcolors.ENDC}")
                    if type(sigs) == list and sigs:
                        result = sigs[0]
                    else:
                        result = sigs

                    log.debug(f"result: {result} type: {type(result)} ")

                    # for key, val in results.items():
                    #     if archive_dir in key:
                    #         log.info(f"FOUND KEY: {key}")
                    #     else:
                    #         log.info(f"NOT FOUND {archive_dir}")
                    # result = results.get(archive_dir)
                    # log.info(f"archive dir {archive_dir} file_path {file_path} result: {result}")
                else:
                    result = results.get(file_path)
        #            if result is None:
        #                for k, v in results.items():
        #                    if str(file_path).startswith(str(k)):
        #                        result = v
        #                        break
                z_log.info(f"{bcolors.DEBUG}scan_engine: {scan_engine} result: {result} {bcolors.ENDC}")
                z_log.debug("Parsing result ")
                if not result:
                    z_log.info(f"{bcolors.DEBUG}file: {file_path} CLEAN {bcolors.ENDC}")
                    scan_signature.append('OK')
                elif isinstance(result, tuple) and any("ERROR" in str(part).upper() for part in result):
                    scan_result = AV_STATUS_ERROR
                    z_log.error(f"{bcolors.FAIL}Scan engine error for file {file_path}: {result} {bcolors.ENDC}")
                    result = result[1]
                    scan_signature.append(result)
                else:
                    scan_result = AV_STATUS_INFECTED
                    z_log.warning(f"{bcolors.WARNING}file: {file_path} INFECTED : {result} {bcolors.ENDC}")
                    if isinstance(result, tuple):
                        result = result[1].split()[0]
                        scan_signature.append(result)
                    else:
                        result = result.split()[0]
                        scan_signature.append(result)

                signature = ":".join(scan_signature)
                z_log.debug(f"scan_engine: {scan_engine} signature: {signature}")

            z_log.info(f"Completed scan of s3://{os.path.join(s3_object.bucket_name, s3_object.key)}")
        except ClientError as e:
            z_log.exception(f"ClientError: Failure getting objects: Client Error: {e} BUCKET: {s3_object.bucket_name}")
            return 1
        except ParamValidationError as e:
            z_log.exception(f"ParamValidationError: Failure getting list of unscanned objects: Parameter validation error: \
                    {e} BUCKET: {s3_object.bucket_name}")
            return 1
        except Exception as e:
            z_log.exception(f"Unexpected error: {e} ")
            return 1
        av_engines = ':'.join(map(str, ret))
        z_log.info(f"AV engines applied: {av_engines}")
        z_log.info(f"AV engines versions: {av_engine_versions}")
        result_time = get_timestamp()
        # Set the properties on the object with the scan results
        input_queue = os.path.basename(input_sqs_queue)
        set_av_tags(s3_client, s3_object, scan_result, signature, result_time, av_engines, av_engine_versions, mime_type, input_queue)
        # WARNING: enabling set_av_metadata without excluding copy from the SQS notification events will put
        # MVS into infinite loop processing the same file over and over again and copy of an object will trigger
        # SQS notification event
        # set_av_metadata(s3_object, scan_result, signature, result_time, av_engines, av_engine_versions, mime_type)
        # Publish the scan results
        """ if AV_STATUS_SNS_ARN not in [None, ""]:
            sns_scan_results(
                sns_client,
                s3_object,
                AV_STATUS_SNS_ARN,
                scan_result,
                signature,
            ) """
        metrics.send(
            env=ENV, bucket=s3_object.bucket_name, key=s3_object.key, status=scan_result
        )
        if scan_result == AV_STATUS_CLEAN:
            # Post sqs message to ouput sqs queue
            postSQSNotification(sqs, message, output_sqs_queue)
            z_log.info(f"CLEAN OBJECT: {s3_object} scan_result: {scan_result} result_time: {result_time}")
        elif scan_result == AV_STATUS_INFECTED:
            # Move Items with infected  results to infected bucket
            move_to_s3_bucket(s3_resource, s3_client, s3_object, INFECTED_BUCKET)
            z_log.warning(f"{bcolors.WARNING} INFECTED OBJECT: {s3_object} scan_result: {scan_result} signature: {signature} result_time: {result_time} {bcolors.ENDC}")
        elif scan_result == AV_STATUS_ERROR:
    # Move or tag file indicating it could not be scanned
            z_log.warning(f"{bcolors.FAIL}UNSCANNED OBJECT: {s3_object} scan_result: {scan_result} reason: scan engine error{bcolors.ENDC}")
            move_to_s3_bucket(s3_resource, s3_client, s3_object, UNSCANNED_BUCKET)
        try:
            z_log.debug(f"Removing: {file_path}")
            if path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            z_log.error(f"{bcolors.FAIL}Error while deleting file {file_path} Reason: {e} {bcolors.ENDC}")
        stop_scan_time = get_timestamp()
        z_log.info(f"Scanning finished at {stop_scan_time}")


def str_to_bool(s):
    return bool(strtobool(str(s)))


def deleteSQSNotification(sqs_client, message, input_sqs_queue):
    try:
        log.debug(f"deleting message: {message}")
        response = sqs_client.delete_message(
            QueueUrl=input_sqs_queue,
            ReceiptHandle=message['ReceiptHandle']
        )
        log.debug(f"SQS message deleted response: {response}")
    except Exception as e:
        log.error(f"Unable to delete sqs message: {message} Reason: {e}")


def postSQSNotification(sqs_client, message, output_sqs_queue):
    try:
        body = message['Body']
        response = sqs_client.send_message(
            QueueUrl=output_sqs_queue,
            MessageBody=body
        )
        log.debug(f" Message posted: {body} ")
        log.debug(f"Response: {response}")
    except Exception as e:
        log.error(f"Unable to send sqs message: {message} Reason: {e}")
