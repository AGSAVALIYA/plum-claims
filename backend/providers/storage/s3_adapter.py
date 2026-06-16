"""AWS S3 storage adapter.

Per planning doc 01_system_architecture.md: Production S3 adapter with
server-side encryption (SSE-S3) and pre-signed URL support.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any

from backend.core.exceptions import StorageProviderError
from backend.core.logging import get_logger
from backend.providers.storage.interface import IStorageProvider, StoredFile

logger = get_logger(__name__)


class S3Adapter(IStorageProvider):
    """Stores files in AWS S3."""

    def __init__(
        self,
        bucket: str = "plum-claims-docs",
        region: str = "ap-south-1",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the boto3 S3 client."""
        if self._client is None:
            try:
                import boto3  # type: ignore[import-untyped]
                from botocore.config import Config  # type: ignore[import-untyped]
            except ImportError:
                raise StorageProviderError(
                    "init",
                    "boto3 is required for S3 storage. Install with: pip install boto3",
                )

            kwargs: dict[str, Any] = {
                "region_name": self.region,
                "config": Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            }
            if self.access_key_id:
                kwargs["aws_access_key_id"] = self.access_key_id
            if self.secret_access_key:
                kwargs["aws_secret_access_key"] = self.secret_access_key

            self._client = boto3.client("s3", **kwargs)

            # Ensure bucket exists (no-op if it does)
            try:
                self._client.head_bucket(Bucket=self.bucket)
            except Exception:
                self._client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration={
                        "LocationConstraint": self.region,
                    },
                )
                logger.info("s3_bucket_created", bucket=self.bucket, region=self.region)

        return self._client

    async def upload(self, file_name: str, content: bytes, content_type: str) -> StoredFile:
        """Upload a file to S3 with SSE-S3 encryption."""
        client = self._get_client()
        file_id = str(uuid.uuid4())[:12]
        ext = Path(file_name).suffix or ""
        object_key = f"claims/{file_id}{ext}"

        try:
            client.upload_fileobj(
                Fileobj=io.BytesIO(content),
                Bucket=self.bucket,
                Key=object_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ServerSideEncryption": "AES256",
                },
            )
            logger.info("s3_upload", key=object_key, size=len(content))
        except Exception as e:
            raise StorageProviderError("upload", str(e))

        return StoredFile(
            file_id=file_id,
            file_name=file_name,
            file_path=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    async def download(self, file_path: str) -> bytes:
        """Download file contents from S3."""
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=file_path)
            data = response["Body"].read()
            return data
        except Exception as e:
            raise StorageProviderError("download", str(e))

    async def delete(self, file_path: str) -> None:
        """Delete a file from S3."""
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=file_path)
            logger.info("s3_delete", key=file_path)
        except Exception as e:
            raise StorageProviderError("delete", str(e))

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        client = self._get_client()
        try:
            client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception:
            return False
