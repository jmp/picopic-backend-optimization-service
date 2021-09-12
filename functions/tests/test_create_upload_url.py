from json import loads
from os import environ
from unittest.mock import patch

from moto import mock_s3
from pytest import fixture


@fixture(scope="function")
def mock_aws():
    environ["AWS_ACCESS_KEY_ID"] = "testing"
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    environ["AWS_SECURITY_TOKEN"] = "testing"
    environ["AWS_SESSION_TOKEN"] = "testing"
    environ["AWS_DEFAULT_REGION"] = "us-east-1"


@mock_s3
@patch.dict(environ, {"BUCKET": "test_bucket", "AWS_REGION": "us-east-1"})
def test_handler(mock_aws):
    from ..create_upload_url.index import handler

    response = handler({}, {})
    body = loads(response["body"])

    assert response["statusCode"] == 200
    assert "fields" in body
    assert "url" in body
    assert "key" in body["fields"]
    assert "policy" in body["fields"]
