from fastapi import APIRouter

from app.modules.workspace.schemas import CreateWorkspaceRequest, Envelope
from app.modules.workspace.service import WorkspaceService

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])
service = WorkspaceService()


@router.post("")
def create_workspace(payload: CreateWorkspaceRequest):
    workspace = service.create_workspace(
        name=payload.name,
        owner_id=payload.owner_id,
        description=payload.description,
    )
    return Envelope(data=workspace.model_dump())


@router.get("")
def list_workspaces():
    workspaces = service.list_workspaces()
    return Envelope(data=[workspace.model_dump() for workspace in workspaces])
