"""Shared repository base classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg


class AsyncpgRepository:
    """Base for performance-critical repos using a raw asyncpg pool."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool


class SupabaseRepository:
    """Base for CRUD repos using the supabase-py async client with raw SQL fallback."""

    def __init__(self, client, pool=None):
        self.client = client
        self.pool = pool
