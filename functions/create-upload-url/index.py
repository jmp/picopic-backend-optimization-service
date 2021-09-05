import json
import os
import uuid

import boto3

s3_client = boto3.client("s3", endpoint_url="https://s3.eu-north-1.amazonaws.com")


def handler(event, context):
    url = s3_client.generate_presigned_post(
        Bucket=os.environ["BUCKET"],
        Key=uuid.uuid4().hex,
        Fields=None,
        Conditions=[["content-length-range", 1, 5_242_880]],
        ExpiresIn=10,
    )
    return {"statusCode": 200, "body": json.dumps(url)}
