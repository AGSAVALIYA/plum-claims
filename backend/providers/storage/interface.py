"""Storage provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StoredFile:
    """Metadata for a stored file."""

    file_id: str
    file_name: str
    file_path: str
    content_type: str
    size_bytes: int


class IStorageProvider(ABC):
    """Interface for file storage (local FS, MinIO, S3)."""

    @abstractmethod
    async def upload(self, file_name: str, content: bytes, content_type: str) -> StoredFile:
        """Upload a file and return its metadata."""
        ...

    @abstractmethod
    async def download(self, file_path: str) -> bytes:
        """Download a file's contents."""
        ...

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        """Delete a file."""
        ...

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        ...
