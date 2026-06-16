"""MinIO (S3-compatible) storage adapter.

Per planning doc 01_system_architecture.md: MinIO adapter for dev/staging
environments that provides an S3-compatible API locally.
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


class MinIOAdapter(IStorageProvider):
    """Stores files in MinIO (S3-compatible object storage)."""

    def __init__(
        self,
        endpoint: str = "minio:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "plum-claims-docs",
        secure: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the MinIO client."""
        if self._client is None:
            try:
                from minio import Minio  # type: ignore[import-untyped]
            except ImportError:
                raise StorageProviderError(
                    "init",
                    "minio package is required for MinIO storage. Install with: pip install minio",
                )
            self._client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            # Ensure bucket exists
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
                logger.info("minio_bucket_created", bucket=self.bucket)
        return self._client

    async def upload(self, file_name: str, content: bytes, content_type: str) -> StoredFile:
        """Upload a file to MinIO."""
        client = self._get_client()
        file_id = str(uuid.uuid4())[:12]
        ext = Path(file_name).suffix or ""
        object_name = f"{file_id}{ext}"

        try:
            client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=io.BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
            logger.info("minio_upload", object_name=object_name, size=len(content))
        except Exception as e:
            raise StorageProviderError("upload", str(e))

        return StoredFile(
            file_id=file_id,
            file_name=file_name,
            file_path=f"{self.bucket}/{object_name}",
            content_type=content_type,
            size_bytes=len(content),
        )

    async def download(self, file_path: str) -> bytes:
        """Download file contents from MinIO.

        file_path should be in the format "bucket/object_name".
        """
        parts = file_path.split("/", 1)
        bucket = parts[0] if len(parts) > 1 else self.bucket
        object_name = parts[1] if len(parts) > 1 else parts[0]

        client = self._get_client()
        try:
            response = client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            raise StorageProviderError("download", str(e))

    async def delete(self, file_path: str) -> None:
        """Delete a file from MinIO."""
        parts = file_path.split("/", 1)
        bucket = parts[0] if len(parts) > 1 else self.bucket
        object_name = parts[1] if len(parts) > 1 else parts[0]

        client = self._get_client()
        try:
            client.remove_object(bucket, object_name)
            logger.info("minio_delete", object_name=object_name)
        except Exception as e:
            raise StorageProviderError("delete", str(e))

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists in MinIO."""
        parts = file_path.split("/", 1)
        bucket = parts[0] if len(parts) > 1 else self.bucket
        object_name = parts[1] if len(parts) > 1 else parts[0]

        client = self._get_client()
        try:
            client.stat_object(bucket, object_name)
            return True
        except Exception:
            return False
