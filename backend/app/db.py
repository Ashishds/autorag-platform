"""Connection management: asyncpg pool (hot path) + Supabase client (CRUD/Auth/Storage).

LLD §5: No ORM. asyncpg for vector search / bulk upserts / bulk reads;
supabase-py for simple CRUD, Auth, Storage, dashboard reads.

Both the asyncpg pool and the Supabase async client contain internal asyncio
primitives (locks, events) that are bound to the event loop they were created
on.  Celery workers and pytest-asyncio tests each run on their own event loop,
so we key every singleton by the running loop — exactly like _pools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    import asyncpg
    from supabase import AsyncClient

import asyncio

_pools: dict[asyncio.AbstractEventLoop, asyncpg.Pool] = {}
# Loop-keyed Supabase client map — same pattern as asyncpg pools.
_supabase_clients: dict[asyncio.AbstractEventLoop, AsyncClient] = {}


async def init_pool() -> asyncpg.Pool:
    """Create the asyncpg pool on app startup (idempotent per event loop)."""
    global _pools
    loop = asyncio.get_running_loop()
    if loop not in _pools:
        import asyncpg

        _pools[loop] = await asyncpg.create_pool(
            dsn=settings.POSTGRES_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
    return _pools[loop]


async def close_pool(all_loops: bool = False) -> None:
    global _pools
    if all_loops:
        for _loop, pool in list(_pools.items()):
            try:
                await pool.close()
            except Exception:
                pass
        _pools.clear()
    else:
        try:
            loop = asyncio.get_running_loop()
            if loop in _pools:
                await _pools[loop].close()
                del _pools[loop]
        except RuntimeError:
            pass


def get_pool() -> asyncpg.Pool:
    try:
        loop = asyncio.get_running_loop()
        if loop in _pools:
            return _pools[loop]
    except RuntimeError:
        pass
    if _pools:
        return next(iter(_pools.values()))
    raise RuntimeError("asyncpg pool not initialized; call init_pool() on startup")


def _supabase_creds_missing() -> bool:
    return (
        not settings.SUPABASE_URL
        or not settings.SUPABASE_SERVICE_ROLE_KEY
        or "your-project" in settings.SUPABASE_URL
        or settings.SUPABASE_SERVICE_ROLE_KEY == "replace-me"
    )


async def init_supabase() -> AsyncClient | None:
    """Create a Supabase async client for the current event loop (idempotent)."""
    global _supabase_clients
    loop = asyncio.get_running_loop()
    if loop in _supabase_clients:
        return _supabase_clients[loop]

    if _supabase_creds_missing():
        # Allow booting without Supabase in local development
        return None

    from supabase import create_async_client

    client = await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )
    _supabase_clients[loop] = client
    return client


async def close_supabase(all_loops: bool = False) -> None:
    """Close the Supabase client(s)."""
    global _supabase_clients
    if all_loops:
        for _loop, client in list(_supabase_clients.items()):
            try:
                await client.postgrest.aclose()
            except Exception:
                pass
        _supabase_clients.clear()
    else:
        try:
            loop = asyncio.get_running_loop()
            if loop in _supabase_clients:
                try:
                    await _supabase_clients[loop].postgrest.aclose()
                except Exception:
                    pass
                del _supabase_clients[loop]
        except RuntimeError:
            pass


def get_supabase() -> AsyncClient:
    """Return the Supabase client for the current event loop.

    Falls back to any available client if the current loop is not registered
    (e.g. synchronous call sites).  Raises RuntimeError when no client exists.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop in _supabase_clients:
            return _supabase_clients[loop]
    except RuntimeError:
        pass
    if _supabase_clients:
        return next(iter(_supabase_clients.values()))
    raise RuntimeError(
        "Supabase client not initialized or credentials missing. "
        "Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set."
    )
