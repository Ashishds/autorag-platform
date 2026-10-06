"""StorageService — Supabase Storage wrapper for document uploads."""

from __future__ import annotations

import asyncio
import os


class StorageService:
    def __init__(self, supabase=None, bucket: str = "documents"):
        self._supabase = supabase
        self._bucket = bucket

    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        if self._supabase is not None:
            await self._supabase.storage.from_(self._bucket).upload(
                path=path, file=content, file_options={"content-type": content_type}
            )
            return path

        # Local disk fallback
        local_dir = os.path.join("storage", os.path.dirname(path))
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join("storage", path)

        def _write():
            with open(local_path, "wb") as f:
                f.write(content)

        await asyncio.to_thread(_write)
        return path

    async def download(self, path: str) -> bytes:
        if self._supabase is not None:
            return await self._supabase.storage.from_(self._bucket).download(path)

        local_path = os.path.join("storage", path)

        def _read():
            with open(local_path, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def delete(self, path: str) -> None:
        if self._supabase is not None:
            await self._supabase.storage.from_(self._bucket).remove([path])
            return

        local_path = os.path.join("storage", path)

        def _remove() -> None:
            if os.path.isfile(local_path):
                os.remove(local_path)

        await asyncio.to_thread(_remove)
