from fastapi import APIRouter, HTTPException

from app.modules.repository.schemas import Envelope, ImportRepositoryRequest, WorkspaceRepositoryListResponse
from app.modules.repository.service import (
    CloneFailedError,
    ProviderNotSupportedError,
    RepositoryImportService,
    RepositoryNotFoundError,
)

router = APIRouter(prefix="/v1/repositories", tags=["repositories"])
service = RepositoryImportService()


@router.post("/import")
def import_repository(payload: ImportRepositoryRequest):
    try:
        repo = service.import_from_url(
            provider=payload.provider,
            remote_url=payload.remote_url,
            workspace_id=payload.workspace_id,
        )
    except CloneFailedError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "REPO_CLONE_FAILED",
                "message": str(exc),
                "http_status": 502,
                "retryable": True,
            },
        ) from exc
    except ProviderNotSupportedError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Unsupported provider: {exc}",
                "http_status": 400,
                "retryable": False,
            },
        ) from exc
    return Envelope(data={"id": repo.id, "status": repo.status.value})


@router.get("")
def list_repositories():
    repos = [service.to_response(repo) for repo in service.list_repositories()]
    return Envelope(data=repos)


@router.get("/workspace/{workspace_id}")
def list_repositories_for_workspace(workspace_id: str):
    repos = [service.to_response(repo) for repo in service.list_repositories_for_workspace(workspace_id)]
    return Envelope(data=WorkspaceRepositoryListResponse(workspace_id=workspace_id, repositories=repos).model_dump())


@router.post("/{repository_id}/analyze")
def analyze_repository(repository_id: str):
    try:
        analysis = service.analyze_repository(repository_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "REPOSITORY_NOT_FOUND",
                "message": f"Repository {repository_id} was not found.",
                "http_status": 404,
                "retryable": False,
            },
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "REPOSITORY_NOT_FOUND",
                "message": str(exc),
                "http_status": 404,
                "retryable": False,
            },
        ) from exc
    return Envelope(data=analysis)


@router.get("/{repository_id}")
def get_repository(repository_id: str):
    try:
        repo = service.get_repository(repository_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "REPOSITORY_NOT_FOUND",
                "message": f"Repository {repository_id} was not found.",
                "http_status": 404,
                "retryable": False,
            },
        ) from exc
    return Envelope(data=service.to_response(repo))
