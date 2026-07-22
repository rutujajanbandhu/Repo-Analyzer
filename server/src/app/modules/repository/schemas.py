import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class ImportRepositoryRequest(BaseModel):
    provider: str
    remote_url: str
    workspace_id: str


class RepositoryResponse(BaseModel):
    id: str
    provider: str
    workspace_id: str
    remote_url: Optional[str] = None
    storage_path: Optional[str] = None
    default_branch: Optional[str] = None
    current_branch: Optional[str] = None
    commit_sha: Optional[str] = None
    file_count: int
    total_bytes: int
    status: str
    created_at: str
    updated_at: str


class DeleteRepositoryResponse(BaseModel):
    id: str
    status: str


class RepositoryAnalysisResponse(BaseModel):
    repository_id: str
    status: str
    summary: dict[str, Any]
    detected_languages: dict[str, int]
    frameworks: list[str]
    entry_points: list[str]
    top_level_directories: list[str]
    notable_files: list[str]
    insights: list[str]


class WorkspaceRepositoryListResponse(BaseModel):
    workspace_id: str
    repositories: list[RepositoryResponse]


class Meta(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"


class Envelope(BaseModel):
    data: Any
    meta: Meta = Field(default_factory=Meta)
