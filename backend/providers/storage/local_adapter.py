"""Local filesystem storage adapter."""

from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
import aiofiles.os as aio_os

from backend.core.exceptions import StorageProviderError
from backend.providers.storage.interface import IStorageProvider, StoredFile


class LocalStorageAdapter(IStorageProvider):
    """Stores files on the local filesystem."""

    def __init__(self, base_path: str = "/workspace/backend/uploads") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, file_name: str, subdir: str = "") -> Path:
        """Resolve a file path, preventing directory traversal."""
        if subdir:
            path = self.base_path / subdir / file_name
        else:
            path = self.base_path / file_name
        path = path.resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise StorageProviderError("upload", "Invalid file path")
        return path

    async def upload(self, file_name: str, content: bytes, content_type: str) -> StoredFile:
        """Upload a file to local storage."""
        file_id = str(uuid.uuid4())[:12]
        ext = Path(file_name).suffix or ""
        stored_name = f"{file_id}{ext}"
        file_path = self._get_path(stored_name)

        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        except Exception as e:
            raise StorageProviderError("upload", str(e))

        return StoredFile(
            file_id=file_id,
            file_name=file_name,
            file_path=str(file_path),
            content_type=content_type,
            size_bytes=len(content),
        )

    async def download(self, file_path: str) -> bytes:
        """Download file contents from local storage."""
        path = self._get_path(file_path)
        if not path.exists():
            raise StorageProviderError("download", f"File not found: {file_path}")
        try:
            async with aiofiles.open(path, "rb") as f:
                return await f.read()
        except Exception as e:
            raise StorageProviderError("download", str(e))

    async def delete(self, file_path: str) -> None:
        """Delete a file from local storage."""
        path = self._get_path(file_path)
        try:
            await aio_os.remove(str(path)) if await aio_os.path.exists(str(path)) else None
        except Exception as e:
            raise StorageProviderError("delete", str(e))

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        path = self._get_path(file_path)
        return path.exists()
