"""Connector cron scheduler — checks for active connectors that need synchronization."""

from __future__ import annotations

import asyncio

from app.workers.celery_app import celery
from app.workers.utils import run_async


@celery.task(name="app.workers.connector_cron.run_connector_scheduler")
def run_connector_scheduler() -> str:
    """Scheduled task to poll for connectors requiring sync."""
    run_async(_check_and_dispatch())
    return "Scheduler run completed"


async def _check_and_dispatch() -> None:
    from app.db import init_pool, init_supabase
    from app.repositories.connector_repo import ConnectorRepository
    from app.workers.connector_task import sync_connector_job
    from datetime import datetime, timezone, timedelta

    pool = await init_pool()
    supabase_client = await init_supabase()
    connector_repo = ConnectorRepository(supabase_client, pool=pool)

    active_connectors = await connector_repo.list_active()
    now = datetime.now(timezone.utc)

    for connector in active_connectors:
        last_synced = connector.get("last_synced_at")
        interval = connector.get("sync_interval_minutes", 60)
        
        # If never synced, or time since last sync >= interval
        if last_synced is None:
            sync_connector_job.delay(str(connector["id"]))
        else:
            # Check if last_synced is a string (datetime parsed from json vs db)
            if isinstance(last_synced, str):
                try:
                    last_synced = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
                except ValueError:
                    continue # Skip invalid format
            
            # Make sure last_synced is timezone aware
            if last_synced.tzinfo is None:
                last_synced = last_synced.replace(tzinfo=timezone.utc)
                
            delta = now - last_synced
            if delta >= timedelta(minutes=interval):
                sync_connector_job.delay(str(connector["id"]))
