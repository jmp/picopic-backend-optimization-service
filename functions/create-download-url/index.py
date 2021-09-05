import json
import logging
import os
from typing import Optional

import boto3
import zopfli
from botocore.client import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3", config=Config(s3={"addressing_style": "path"}))

PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
ALLOWED_FILE_TYPES = {"image/png": "png"}


def handler(event, context):
    bucket = os.environ["BUCKET"]
    key = event["pathParameters"]["key"]
    logger.info("Getting object %s from bucket %s.", key, bucket)
    original_object = s3_client.get_object(Bucket=bucket, Key=key)
    logger.info("Reading object body.")
    body = original_object["Body"].read()
    logger.info("Verifying image type.")
    mime = _guess_mime_type(body)
    if mime not in ALLOWED_FILE_TYPES.keys():
        logger.warning("Attempted to optimize invalid file type %s.", mime)
        logger.info("Deleting invalid object %s...", key)
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info("Invalid object %s deleted.", key)
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "File type not allowed."}),
        }
    logger.info("File type detected as %s.", mime)
    logger.info("Optimizing %s bytes...", len(body))
    optimized_body = _optimize(body)
    if optimized_body is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Image could not be optimized."}),
        }
    logger.info("Optimized to %s bytes.", len(optimized_body))
    logger.info("Putting optimized object %s to bucket %s.", key, bucket)
    s3_client.put_object(Bucket=bucket, Key=key, Body=optimized_body)
    logger.info("Generating presigned URL.")
    download_filename = f"optimized.{ALLOWED_FILE_TYPES[mime]}"
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ResponseContentDisposition": f"attachment; filename={download_filename}",
        },
        ExpiresIn=10,
    )
    logger.info("Presigned URL created; returning successfully.")
    return {"statusCode": 200, "body": json.dumps({"url": url})}


def _guess_mime_type(data: bytes) -> str:
    if data[:8] == PNG_HEADER:
        return "image/png"
    return "application/octet-stream"


def _optimize(data: bytes) -> Optional[bytes]:
    try:
        png = zopfli.ZopfliPNG()
        optimized_data = png.optimize(data)
        if optimized_data[:8] != PNG_HEADER:
            logger.error("Invalid optimized image: %s", optimized_data)
            raise ValueError("Corrupted PNG generated.")
        return optimized_data
    except ValueError:
        logger.exception("Failed to optimize image.")
    return None
