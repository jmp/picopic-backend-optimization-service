from base64 import b64decode
from json import loads
from os import environ
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from moto import mock_s3
from pytest import fixture, raises

TEST_BUCKET = "test_bucket"

UNOPTIMIZED_TEST_IMAGE = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAEU"
    "lEQVR42mNk+A+EQMAIYwAAKgMD/yQkuNAAAAAASUVORK5CYII="
)

OPTIMIZED_TEST_IMAGE = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAADk"
    "lEQVR4AWNg+A9CUAoAG/ID/Wg9+UgAAAAASUVORK5CYII="
)

INVALID_TEST_IMAGE = b64decode("iVBORw0KGgoA")


@fixture(scope="function")
def aws_credentials():
    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_SECURITY_TOKEN"] = "testing"
    environ["AWS_SESSION_TOKEN"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-east-1"


@fixture(scope="function")
def s3(aws_credentials):
    with mock_s3():
        conn = boto3.resource("s3")
        conn.create_bucket(Bucket="test_bucket")
        yield boto3.client("s3")


@patch.dict(environ, {"BUCKET": TEST_BUCKET})
def test_handler_returns_download_url_when_image_is_valid(s3):
    from create_download_url.index import handler

    # Given that a valid test image exists in the bucket
    bucket = environ["BUCKET"]
    key = "1a2d894fed4b40f695bf44f8f645c233"
    s3.put_object(Bucket=bucket, Key=key, Body=UNOPTIMIZED_TEST_IMAGE)

    # When the handler is run
    response = handler({"pathParameters": {"key": key}}, {})

    # Then the request should successfully return a download URL
    body = loads(response["body"])
    assert response["statusCode"] == 200
    assert body["url"].startswith(f"https://s3.amazonaws.com/{bucket}/{key}")
    # The object should have been replaced with optimized image
    obj = s3.get_object(Bucket=bucket, Key=key)
    assert obj["Body"].read() == OPTIMIZED_TEST_IMAGE


@patch.dict(environ, {"BUCKET": TEST_BUCKET})
def test_handler_returns_error_when_file_type_is_forbidden(s3):
    from create_download_url.index import handler

    # Given that a file of forbidden type exists in the bucket
    bucket = environ["BUCKET"]
    key = "bb6c2b439fa846d4983f00cc6de47a41"
    s3.put_object(Bucket=bucket, Key=key, Body=b"invalid")

    # When the handler is run
    response = handler({"pathParameters": {"key": key}}, {})

    # Then the request should return status code 400 with error message
    body = loads(response["body"])
    assert response["statusCode"] == 400
    assert body == {"message": "File type not allowed."}
    # The object should have been deleted
    with raises(ClientError) as exception_info:
        s3.get_object(Bucket=bucket, Key=key)
    assert exception_info.typename == "NoSuchKey"


@patch.dict(environ, {"BUCKET": TEST_BUCKET})
def test_handler_returns_error_when_optimization_fails(s3):
    from create_download_url.index import handler

    # Given that an corrupted image of allowed type exists in the bucket
    bucket = environ["BUCKET"]
    key = "8b6a7d55e1ad440bb84eee2cf5773522"
    s3.put_object(Bucket=bucket, Key=key, Body=INVALID_TEST_IMAGE)

    # When the handler is run
    response = handler({"pathParameters": {"key": key}}, {})

    # Then the request should return status code 400 with error message
    body = loads(response["body"])
    assert response["statusCode"] == 400
    assert body == {"message": "Image could not be optimized."}
    # The object should have been deleted
    with raises(ClientError) as exception_info:
        s3.get_object(Bucket=bucket, Key=key)
    assert exception_info.typename == "NoSuchKey"
