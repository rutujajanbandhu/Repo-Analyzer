from fastapi import APIRouter

from app.modules.repository.api import service as repository_service
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


@router.get("/{workspace_id}/repositories")
def list_workspace_repositories(workspace_id: str):
    repos = [repository_service.to_response(repo) for repo in repository_service.list_repositories_for_workspace(workspace_id)]
    return Envelope(data=repos)
