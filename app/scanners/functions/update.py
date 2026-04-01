# -*- coding: utf-8 -*-
# Upside Travel, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import boto3

from functions import clamav

from functions.common import AV_DEFINITION_PATH
from functions.common import AV_DEFINITION_S3_BUCKET
from functions.common import AV_DEFINITION_S3_PREFIX
from functions.common import CLAMAVLIB_PATH
from functions.common import ACCESS_KEY_ID
from functions.common import SECRET_ACCESS_KEY
from functions.common import AWS_DEFAULT_REGION
from functions.common import get_timestamp
from functions.common import bcolors


def start_process():
    s3 = boto3.resource("s3",
                        aws_access_key_id=ACCESS_KEY_ID,
                        aws_secret_access_key=SECRET_ACCESS_KEY)
    s3_client = boto3.client("s3",
                             region_name=AWS_DEFAULT_REGION,
                             aws_access_key_id=ACCESS_KEY_ID,
                             aws_secret_access_key=SECRET_ACCESS_KEY)

    print("Script starting at %s\n" % (get_timestamp()))
    to_download = clamav.update_defs_from_s3(
        s3_client, AV_DEFINITION_S3_BUCKET, AV_DEFINITION_S3_PREFIX
    )

    for download in to_download.values():
        s3_path = download["s3_path"]
        local_path = download["local_path"]
        print("Downloading definition file %s from s3://%s" % (local_path, s3_path))
        s3.Bucket(AV_DEFINITION_S3_BUCKET).download_file(s3_path, local_path)
        print("Downloading definition file %s complete!" % local_path)

    print(f"{bcolors.WARNING}Starting to update defs from freshclam{bcolors.ENDC}")
    clamav.update_defs_from_freshclam(AV_DEFINITION_PATH, CLAMAVLIB_PATH)
    # If main.cvd gets updated (very rare), we will need to force freshclam
    # to download the compressed version to keep file sizes down.
    # The existence of main.cud is the trigger to know this has happened.
    if os.path.exists(os.path.join(AV_DEFINITION_PATH, "main.cud")):
        os.remove(os.path.join(AV_DEFINITION_PATH, "main.cud"))
        print("Removed %s%s\n" % (AV_DEFINITION_PATH, "main.cud"))
        if os.path.exists(os.path.join(AV_DEFINITION_PATH, "main.cvd")):
            os.remove(os.path.join(AV_DEFINITION_PATH, "main.cvd"))
            print("Removed %s%s\n" % (AV_DEFINITION_PATH, "main.cvd"))
        clamav.update_defs_from_freshclam(AV_DEFINITION_PATH, CLAMAVLIB_PATH)
    clamav.upload_defs_to_s3(
        s3_client, AV_DEFINITION_S3_BUCKET, AV_DEFINITION_S3_PREFIX, AV_DEFINITION_PATH
    )
    print("Script finished at %s\n" % get_timestamp())
