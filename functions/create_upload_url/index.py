from json import dumps
from os import environ
from secrets import token_urlsafe

from boto3 import client

s3_client = client(
    "s3", endpoint_url=f"https://s3.{environ['AWS_REGION']}.amazonaws.com"
)


def handler(event, context):
    url = s3_client.generate_presigned_post(
        Bucket=environ["BUCKET"],
        Key=token_urlsafe(),
        Fields=None,
        Conditions=[["content-length-range", 1, 1_048_576]],
        ExpiresIn=10,
    )
    return {
        "statusCode": 200,
        "body": dumps(url),
    }
