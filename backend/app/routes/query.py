"""Query FastPath route (SSE-capable). LLD §6.2."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_query_service
from app.schemas.common import APIResponse
from app.schemas.query import QueryRequest, QueryResult
from app.services.query_service import QueryService

router = APIRouter()


@router.post("", response_model=APIResponse[QueryResult])
async def query(
    req: QueryRequest,
    svc: QueryService = Depends(get_query_service),
) -> APIResponse[QueryResult]:
    print(f">>> [Query Route] Received query request. pipeline_id={req.pipeline_id}, q='{req.q}'", flush=True)
    try:
        result = await svc.query(req)
        print(f">>> [Query Route] Query succeeded in {result.latency_ms}ms.", flush=True)
        return APIResponse.ok(result)
    except Exception as e:
        import traceback
        print(f">>> [Query Route] Query failed with error: {e}", flush=True)
        traceback.print_exc()
        raise
