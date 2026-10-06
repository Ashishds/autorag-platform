"""Connector worker task — synchronizes external sources (S3, Web)."""

from __future__ import annotations

import asyncio
import uuid
import json
import httpx
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import aioboto3

from app.workers.celery_app import celery
from app.workers.utils import run_async


@celery.task(name="app.workers.connector_task.sync_connector_job", bind=True, max_retries=3)
def sync_connector_job(self, connector_id: str) -> dict:
    return run_async(_run_sync(uuid.UUID(connector_id)))


async def _run_sync(connector_id: uuid.UUID) -> dict:
    from app.db import init_pool, init_supabase
    from app.repositories.connector_repo import ConnectorRepository
    from app.repositories.document_repo import DocumentRepository
    from app.repositories.pipeline_repo import PipelineRepository
    from app.services.storage_service import StorageService
    from app.workers.ingest_task import dispatch_ingestion
    from app.schemas.tasks import IngestTaskPayload

    pool = await init_pool()
    supabase_client = await init_supabase()

    connector_repo = ConnectorRepository(supabase_client, pool=pool)
    doc_repo = DocumentRepository(supabase_client, pool=pool)
    pipeline_repo = PipelineRepository(supabase_client, pool=pool)
    storage_svc = StorageService(supabase_client)

    connector = await connector_repo.get(connector_id)
    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    pipeline = await pipeline_repo.get(connector["pipeline_id"])
    if not pipeline:
        raise ValueError(f"Pipeline {connector['pipeline_id']} not found")

    c_type = connector["type"]
    config = connector.get("config", {})
    org_id = connector["organization_id"]
    pipeline_id = connector["pipeline_id"]
    
    # Get existing documents for this connector to track deletions
    existing_docs = await doc_repo.list_by_pipeline(pipeline_id)
    existing_source_map = {
        d["source_id"]: d for d in existing_docs 
        if d.get("connector_id") == str(connector_id) and d.get("source_id")
    }
    
    processed_source_ids = set()

    try:
        await connector_repo.update(connector_id, {"status": "active"})

        if c_type == "s3":
            bucket = config.get("bucket")
            prefix = config.get("prefix", "")
            aws_access_key_id = config.get("aws_access_key_id")
            aws_secret_access_key = config.get("aws_secret_access_key")
            region = config.get("region_name", "us-east-1")
            
            session = aioboto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region
            )
            async with session.client("s3") as s3:
                paginator = s3.get_paginator('list_objects_v2')
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get('Contents', []):
                        key = obj['Key']
                        if key.endswith('/'):
                            continue
                        
                        source_id = f"s3://{bucket}/{key}"
                        processed_source_ids.add(source_id)
                        
                        if source_id in existing_source_map:
                            continue # Already ingested, could check ETag/LastModified here
                            
                        # Download and ingest
                        obj_resp = await s3.get_object(Bucket=bucket, Key=key)
                        content = await obj_resp['Body'].read()
                        
                        filename = key.split('/')[-1]
                        document_id = uuid.uuid4()
                        storage_path = f"{org_id}/{document_id}/{filename}"
                        mime_type = obj_resp.get('ContentType', 'application/octet-stream')
                        
                        await storage_svc.upload(storage_path, content, mime_type)
                        
                        doc_row = {
                            "id": document_id,
                            "organization_id": org_id,
                            "pipeline_id": pipeline_id,
                            "filename": filename,
                            "file_size": len(content),
                            "storage_path": storage_path,
                            "status": "queued",
                            "mime_type": mime_type,
                            "connector_id": str(connector_id),
                            "source_id": source_id,
                        }
                        await doc_repo.create(doc_row)
                        
                        payload = IngestTaskPayload(
                            document_id=document_id,
                            pipeline_id=pipeline_id,
                            organization_id=org_id,
                            storage_path=storage_path,
                            chunking_strategy=pipeline["chunking_strategy"],
                        )
                        dispatch_ingestion(payload)

        elif c_type == "web":
            base_url = config.get("url")
            max_depth = int(config.get("max_depth", 3))
            
            visited = set()
            queue = [(base_url, 0)]
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                while queue:
                    url, depth = queue.pop(0)
                    if url in visited:
                        continue
                    visited.add(url)
                    
                    source_id = url
                    processed_source_ids.add(source_id)
                    
                    if source_id not in existing_source_map:
                        try:
                            resp = await client.get(url, follow_redirects=True)
                            if resp.status_code == 200:
                                content = resp.content
                                parsed_url = urlparse(url)
                                clean_path = parsed_url.path.strip("/").replace("/", "_")
                                filename = parsed_url.netloc + ("_" + clean_path if clean_path else "")
                                if not filename.endswith(".html"):
                                    filename += ".html"
                                mime_type = "text/html"
                                
                                document_id = uuid.uuid4()
                                storage_path = f"{org_id}/{document_id}/{filename}"
                                
                                await storage_svc.upload(storage_path, content, mime_type)
                                
                                doc_row = {
                                    "id": document_id,
                                    "organization_id": org_id,
                                    "pipeline_id": pipeline_id,
                                    "filename": filename,
                                    "file_size": len(content),
                                    "storage_path": storage_path,
                                    "status": "queued",
                                    "mime_type": mime_type,
                                    "connector_id": str(connector_id),
                                    "source_id": source_id,
                                }
                                await doc_repo.create(doc_row)
                                
                                payload = IngestTaskPayload(
                                    document_id=document_id,
                                    pipeline_id=pipeline_id,
                                    organization_id=org_id,
                                    storage_path=storage_path,
                                    chunking_strategy=pipeline["chunking_strategy"],
                                )
                                dispatch_ingestion(payload)
                                
                                if depth < max_depth:
                                    soup = BeautifulSoup(content, 'html.parser')
                                    for link in soup.find_all('a', href=True):
                                        next_url = urljoin(url, link['href'])
                                        if urlparse(next_url).netloc == parsed_url.netloc:
                                            queue.append((next_url, depth + 1))
                        except Exception as e:
                            # Log and continue
                            pass
        elif c_type in ["google_drive", "notion", "dropbox", "onedrive", "sharepoint"]:
            from app.workers.connectors import get_handler
            from app.config import settings
            
            handler = get_handler(c_type)
            if handler:
                async def ingest_file_cb(content, filename, mime_type, source_id):
                    document_id = uuid.uuid4()
                    storage_path = f"{org_id}/{document_id}/{filename}"
                    await storage_svc.upload(storage_path, content, mime_type)
                    doc_row = {
                        "id": document_id,
                        "organization_id": org_id,
                        "pipeline_id": pipeline_id,
                        "filename": filename,
                        "file_size": len(content),
                        "storage_path": storage_path,
                        "status": "queued",
                        "mime_type": mime_type,
                        "connector_id": str(connector_id),
                        "source_id": source_id,
                    }
                    await doc_repo.create(doc_row)
                    payload = IngestTaskPayload(
                        document_id=document_id,
                        pipeline_id=pipeline_id,
                        organization_id=org_id,
                        storage_path=storage_path,
                        chunking_strategy=pipeline["chunking_strategy"],
                    )
                    dispatch_ingestion(payload)
                    
                client_id = settings.GOOGLE_CLIENT_ID if c_type == "google_drive" else settings.NOTION_CLIENT_ID
                client_secret = settings.GOOGLE_CLIENT_SECRET if c_type == "google_drive" else settings.NOTION_CLIENT_SECRET
                
                deps = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "ingest_file": ingest_file_cb
                }
                
                await handler.sync(connector, pipeline, existing_source_map, processed_source_ids, deps)
        
        # Deletion logic: Delete documents that exist in DB but were not found in source
        for source_id, doc in existing_source_map.items():
            if source_id not in processed_source_ids:
                doc_id = uuid.UUID(doc["id"])
                
                # Delete from storage if possible
                storage_path = doc.get("storage_path")
                if storage_path:
                    try:
                        await storage_svc.delete(storage_path)
                    except Exception:
                        pass
                
                # Delete from document repository (cascades to chunks)
                await doc_repo.delete(doc_id)

        # Update last_synced_at
        from datetime import datetime, timezone
        await connector_repo.update(connector_id, {"last_synced_at": datetime.now(timezone.utc)})

        return {"connector_id": str(connector_id), "status": "completed"}
        
    except Exception as exc:
        error_msg = str(exc)
        await connector_repo.update(connector_id, {"status": "error"})
        return {"connector_id": str(connector_id), "status": "error", "error": error_msg}
