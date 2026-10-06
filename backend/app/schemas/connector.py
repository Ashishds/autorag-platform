from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class ConnectorType(str, Enum):
    s3 = "s3"
    web = "web"
    google_drive = "google_drive"
    notion = "notion"
    dropbox = "dropbox"
    onedrive = "onedrive"
    sharepoint = "sharepoint"


class ConnectorStatus(str, Enum):
    active = "active"
    paused = "paused"
    error = "error"


class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: ConnectorType
    pipeline_id: UUID
    config: dict[str, Any] = Field(default_factory=dict)
    sync_interval_minutes: int = 60


class ConnectorUpdate(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    sync_interval_minutes: int | None = None
    status: ConnectorStatus | None = None


class ConnectorOut(BaseModel):
    id: UUID
    organization_id: UUID
    pipeline_id: UUID
    name: str
    type: str
    config: dict[str, Any]
    status: str
    last_synced_at: datetime | None = None
    sync_interval_minutes: int
    auth_url: str | None = None
    oauth_state: str | None = None
    created_at: datetime
    updated_at: datetime
