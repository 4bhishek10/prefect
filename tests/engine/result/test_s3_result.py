from unittest.mock import MagicMock, patch

import cloudpickle
import pytest

import prefect
from prefect.engine.result import S3Result
from prefect.utilities.configuration import set_temporary_config


# @pytest.mark.xfail(raises=ImportError, reason="aws extras not installed.")
class TestS3Result:
    @pytest.fixture
    def session(self, monkeypatch):
        import boto3

        session = MagicMock()
        with patch.dict("sys.modules", {"boto3": MagicMock(session=session)}):
            yield session

    def test_s3_client_init_uses_secrets(self, session):
        result = S3Result(bucket="bob", credentials_secret="AWS_CREDENTIALS")
        assert result.bucket == "bob"
        assert session.Session().client.called is False

        with prefect.context(
            secrets=dict(AWS_CREDENTIALS=dict(ACCESS_KEY=1, SECRET_ACCESS_KEY=42))
        ):
            with set_temporary_config({"cloud.use_local_secrets": True}):
                result.initialize_client()
        assert session.Session().client.call_args[1] == {
            "aws_access_key_id": 1,
            "aws_secret_access_key": 42,
        }

    def test_s3_client_init_uses_custom_secrets(self, session):
        result = S3Result(bucket="bob", credentials_secret="MY_FOO")

        with prefect.context(
            secrets=dict(MY_FOO=dict(ACCESS_KEY=1, SECRET_ACCESS_KEY=999))
        ):
            with set_temporary_config({"cloud.use_local_secrets": True}):
                result.initialize_client()

        assert result.bucket == "bob"
        assert session.Session().client.call_args[1] == {
            "aws_access_key_id": 1,
            "aws_secret_access_key": 999,
        }

    def test_s3_writes_to_blob_with_rendered_filename(self, session):
        result = S3Result(
            value="so-much-data", bucket="foo", filename_template="{thing}/here.txt"
        )

        with prefect.context(
            secrets=dict(AWS_CREDENTIALS=dict(ACCESS_KEY=1, SECRET_ACCESS_KEY=42)),
            thing="yes!",
        ):
            with set_temporary_config({"cloud.use_local_secrets": True}):
                uri = result.write()

        used_uri = session.Session().client.return_value.upload_fileobj.call_args[1][
            "Key"
        ]

        assert used_uri == uri
        assert used_uri.startswith("yes!/here.txt")

    def test_s3_result_is_pickleable(self, monkeypatch):
        class client:
            def __init__(self, *args, **kwargs):
                pass

            def __getstate__(self):
                raise ValueError("I cannot be pickled.")

        import boto3

        with patch.dict("sys.modules", {"boto3": MagicMock()}):
            boto3.session.Session().client = client

            with prefect.context(
                secrets=dict(AWS_CREDENTIALS=dict(ACCESS_KEY=1, SECRET_ACCESS_KEY=42))
            ):
                with set_temporary_config({"cloud.use_local_secrets": True}):
                    result = S3Result(bucket="foo")
            res = cloudpickle.loads(cloudpickle.dumps(result))
            assert isinstance(res, S3Result)

    def test_s3_result_does_not_exist(self, session):
        import botocore

        exc = botocore.exceptions.ClientError(
            {"Error": {"Code": "404"}}, "list_objects"
        )

        class _client:
            def __init__(self, *args, **kwargs):
                pass

            def get_object(self, *args, **kwargs):
                raise exc

        session.Session().client = _client
        result = S3Result(bucket="bob", filename_template="stuff")

        assert result.exists() == False

    def test_s3_result_exists(self, session):
        import botocore

        exc = botocore.exceptions.ClientError(
            {"Error": {"Code": "404"}}, "list_objects"
        )

        class _client:
            def __init__(self, *args, **kwargs):
                pass

            def get_object(self, *args, **kwargs):
                return MagicMock()

        session.Session().client = _client
        result = S3Result(bucket="bob", filename_template="stuff")

        assert result.exists() == True
