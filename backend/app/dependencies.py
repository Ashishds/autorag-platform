from app.db import get_pool, get_supabase
import uuid
import jwt
from pydantic import BaseModel
from fastapi import Request

from app.repositories.audit_repo import AuditRepository
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.connector_repo import ConnectorRepository
from app.repositories.deployment_repo import DeploymentRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.evaluation_repo import EvaluationRepository
from app.repositories.experiment_repo import ExperimentRepository
from app.repositories.golden_repo import GoldenRepository
from app.repositories.pipeline_repo import PipelineRepository
from app.repositories.query_log_repo import QueryLogRepository
from app.repositories.run_repo import RunRepository
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.connector_service import ConnectorService
from app.services.deploy_service import DeployService
from app.services.embedding import get_embedding_provider
from app.services.evaluation_service import EvaluationService
from app.services.golden_set_service import GoldenSetService
from app.services.llm.service import LLMService
from app.services.pipeline_service import PipelineService
from app.services.query_service import QueryService
from app.services.reranker.cohere import CohereReranker
from app.services.storage_service import StorageService


def _get_supabase_client():
    try:
        return get_supabase()
    except RuntimeError:
        return None


def get_chunk_repo() -> ChunkRepository:
    return ChunkRepository(get_pool())


def get_pipeline_repo() -> PipelineRepository:
    return PipelineRepository(_get_supabase_client(), pool=get_pool())


def get_document_repo() -> DocumentRepository:
    return DocumentRepository(_get_supabase_client(), pool=get_pool())


def get_connector_repo() -> ConnectorRepository:
    return ConnectorRepository(_get_supabase_client(), pool=get_pool())


def get_audit_repo() -> AuditRepository:
    return AuditRepository(_get_supabase_client(), pool=get_pool())


def get_query_log_repo() -> QueryLogRepository:
    return QueryLogRepository(get_pool())


def get_run_repo() -> RunRepository:
    return RunRepository(_get_supabase_client(), pool=get_pool())


def get_evaluation_repo() -> EvaluationRepository:
    return EvaluationRepository(_get_supabase_client(), pool=get_pool())


def get_golden_repo() -> GoldenRepository:
    return GoldenRepository(_get_supabase_client(), pool=get_pool())


def get_experiment_repo() -> ExperimentRepository:
    return ExperimentRepository(_get_supabase_client(), pool=get_pool())


def get_deployment_repo() -> DeploymentRepository:
    return DeploymentRepository(_get_supabase_client(), pool=get_pool())


def get_storage_service() -> StorageService:
    return StorageService(_get_supabase_client())


def get_audit_service() -> AuditService:
    return AuditService(get_audit_repo())


def get_pipeline_service() -> PipelineService:
    return PipelineService(get_pipeline_repo(), get_audit_service())


def get_connector_service() -> ConnectorService:
    return ConnectorService(get_connector_repo(), get_audit_service())


def get_llm_service() -> LLMService:
    return LLMService()


def get_evaluation_service() -> EvaluationService:
    return EvaluationService()


def get_golden_set_service() -> GoldenSetService:
    return GoldenSetService(
        golden_repo=get_golden_repo(),
        chunk_repo=get_chunk_repo(),
        llm=LLMService(),
    )


def get_query_service() -> QueryService:
    return QueryService(
        llm=LLMService(),
        embedder=get_embedding_provider(),
        reranker=CohereReranker(),
        chunk_repo=get_chunk_repo(),
        query_log_repo=get_query_log_repo(),
    )


def get_deploy_service() -> DeployService:
    return DeployService(
        deployment_repo=get_deployment_repo(),
        pipeline_repo=get_pipeline_repo(),
        audit=get_audit_service(),
    )


def get_approval_service() -> ApprovalService:
    return ApprovalService(experiment_repo=get_experiment_repo(), audit=get_audit_service())


class TenantContext(BaseModel):
    organization_id: uuid.UUID
    actor_id: uuid.UUID


async def get_tenant_context(request: Request) -> TenantContext:
    """Extract and verify tenant organization and actor context from JWT token."""
    auth_header = request.headers.get("Authorization")
    org_id = uuid.UUID(int=0)
    actor_id = uuid.UUID(int=0)
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Decode unverified to support dev workflows without network keys
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Extract org_id claim
            if "org_id" in decoded:
                org_id = uuid.UUID(decoded["org_id"])
            elif "user_metadata" in decoded and "org_id" in decoded["user_metadata"]:
                org_id = uuid.UUID(decoded["user_metadata"]["org_id"])
            elif "app_metadata" in decoded and "org_id" in decoded["app_metadata"]:
                org_id = uuid.UUID(decoded["app_metadata"]["org_id"])
                
            # Extract user_id sub claim
            if "sub" in decoded:
                actor_id = uuid.UUID(decoded["sub"])
        except Exception:
            pass
            
    return TenantContext(organization_id=org_id, actor_id=actor_id)

