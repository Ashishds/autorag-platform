"""Utility helpers for Celery workers."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run an async coroutine synchronously, compatible with running event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        result_future = Future()

        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                val = new_loop.run_until_complete(coro)
                result_future.set_result(val)
            except Exception as e:
                result_future.set_exception(e)
            finally:
                try:
                    from app.db import close_pool

                    new_loop.run_until_complete(close_pool())
                except Exception:
                    pass
                new_loop.close()

        t = threading.Thread(target=run_in_thread)
        t.start()
        return result_future.result()
    else:
        return asyncio.run(coro)
