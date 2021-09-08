from json import dumps
from logging import INFO, getLogger
from os import environ
from typing import Optional

from boto3 import client
from botocore.client import Config
from zopfli import ZopfliPNG

logger = getLogger()
logger.setLevel(INFO)
s3_client = client("s3", config=Config(s3={"addressing_style": "path"}))

PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
ALLOWED_FILE_TYPES = {"image/png": "png"}


def handler(event, context):
    bucket = environ["BUCKET"]
    key = event["pathParameters"]["key"]
    original_object = s3_client.get_object(Bucket=bucket, Key=key)
    body = original_object["Body"].read()
    mime = _guess_mime_type(body)
    if mime not in ALLOWED_FILE_TYPES.keys():
        s3_client.delete_object(Bucket=bucket, Key=key)
        return {
            "statusCode": 400,
            "body": dumps({"message": "File type not allowed."}),
        }
    optimized_body = _optimize(body)
    if optimized_body is None:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return {
            "statusCode": 400,
            "body": dumps({"message": "Image could not be optimized."}),
        }
    s3_client.put_object(Bucket=bucket, Key=key, Body=optimized_body)
    filename = f"optimized.{ALLOWED_FILE_TYPES[mime]}"
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ResponseContentDisposition": f"attachment; filename={filename}",
        },
        ExpiresIn=10,
    )
    return {"statusCode": 200, "body": dumps({"url": url})}


def _guess_mime_type(data: bytes) -> str:
    """Returns the MIME type based on magic bytes."""
    if data.startswith(PNG_HEADER):
        return "image/png"
    return "application/octet-stream"


def _optimize(data: bytes) -> Optional[bytes]:
    """Optimizes the given image."""
    try:
        return ZopfliPNG().optimize(data)
    except ValueError:
        logger.exception("Failed to optimize image.")
        return None
