import json
import traceback

from datetime import datetime
from functions.common import SLACK_CHANNEL
from functions.common import SLACK_USER
from functions.common import SLACK_ENDPOINT
from functions.provider_info import search_files

import urllib3
http = urllib3.PoolManager()


def slack_notify(s3_object, object_size, mime_type, input_queue, z_log):
    dateTimeObj = datetime.now()
    slack_msg = ""
    timestamp = dateTimeObj.strftime("%b-%d-%Y (%H:%M:%S.%f)")
    # Get the object information from the s3 object
    message = f"LARGE FILE SCAN ALERT:\nSCAN TIME: {timestamp} \nINPUT BUCKET: {s3_object.bucket_name}\nS3 KEY: {s3_object.key}\nSIZE: {object_size} GB \nMIME TYPE: {mime_type}\nSQS NAME: {input_queue}"
    z_log.info(f"file info: {message}")
    try:
        provider_info = search_files(s3_object.bucket_name, s3_object.key, z_log, range=1)
        slack_msg = message + provider_info
        z_log.info(f"slack message: {slack_msg}")
        post_slack_Message(slack_msg, s3_object.key, z_log)
        return
    except Exception as e:
        tb = traceback.format_stack(limit=5)
        z_log.error(e)
        z_log.error(f"error posting slack message: {slack_msg} Bucket: {s3_object.bucket_name} S3 Key: {s3_object.key} \
            Obj_size: {object_size} GB, \n Traceback: {str(tb)}")


def post_slack_Message(message, key, z_log):

    if not message:
        z_log.info("Slack Message body is empty, No message will be published.")
        return
    msg = {
        "channel": SLACK_CHANNEL,
        "username": SLACK_USER,
        "text": message,
        "icon_emoji": ":satellite:"
    }
    try:
        encoded_msg = json.dumps(msg).encode('utf-8')
        resp = http.request('POST', SLACK_ENDPOINT, body=encoded_msg)
        z_log.info({
            "message": encoded_msg,
            "status_code": resp.status,
            "response": resp.data
        })
    except Exception as e:
        z_log.error(f"error posting slack message: {encoded_msg} due to: {e}")
