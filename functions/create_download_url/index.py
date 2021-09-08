from json import dumps
from logging import INFO, getLogger
from os import environ
from typing import Optional

from boto3 import client
from botocore.client import Config
from botocore.exceptions import ClientError
from zopfli import ZopfliPNG

logger = getLogger()
logger.setLevel(INFO)
s3_client = client("s3", config=Config(s3={"addressing_style": "path"}))

PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
ALLOWED_FILE_TYPES = {"image/png": "png"}


def handler(event, context):
    bucket = environ["BUCKET"]
    key = event["pathParameters"]["key"]

    # Fetch the object from the bucket
    body = _get_object_by_key(key, bucket)
    if body is None:
        return _error("Image does not exist.", status=404)

    # Detect the file type
    mime = _guess_mime_type(body)
    if mime not in ALLOWED_FILE_TYPES.keys():
        s3_client.delete_object(Bucket=bucket, Key=key)
        return _error("File type not allowed.")

    # Optimize the image
    optimized_body = _optimize(body)
    if optimized_body is None:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return _error("Image could not be optimized.")

    # Overwrite the original image with the optimized one
    s3_client.put_object(Bucket=bucket, Key=key, Body=optimized_body)

    # Generate presigned URL for downloading the file from S3
    url = _create_download_url(key, bucket, mime)

    return {
        "statusCode": 200,
        "body": dumps({"url": url}),
    }


def _get_object_by_key(key: str, bucket: str) -> Optional[bytes]:
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise
    body = obj["Body"].read()
    return body


def _create_download_url(key: str, bucket: str, mime: str) -> dict:
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
    return url


def _error(message: str, status: int = 400) -> dict:
    return {
        "statusCode": status,
        "body": dumps({"message": message}),
    }


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
