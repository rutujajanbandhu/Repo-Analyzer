import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateWorkspaceRequest(BaseModel):
    name: str
    owner_id: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    description: Optional[str] = None
    status: str = "active"


class Meta(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"


class Envelope(BaseModel):
    data: Any
    meta: Meta = Field(default_factory=Meta)
