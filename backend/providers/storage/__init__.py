"""Storage provider — local filesystem, MinIO (S3-compatible), and AWS S3 adapters."""

from backend.providers.storage.interface import IStorageProvider, StoredFile
from backend.providers.storage.local_adapter import LocalStorageAdapter
from backend.providers.storage.minio_adapter import MinIOAdapter
from backend.providers.storage.s3_adapter import S3Adapter

__all__ = [
    "IStorageProvider",
    "LocalStorageAdapter",
    "MinIOAdapter",
    "S3Adapter",
    "StoredFile",
]
