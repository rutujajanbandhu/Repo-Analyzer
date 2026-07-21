import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.modules.repository.models import Provider, Repository, RepositoryStatus, REPOSITORY_STORE
from app.modules.repository.schemas import DeleteRepositoryResponse, RepositoryResponse

STORAGE_ROOT = Path(__file__).resolve().parents[3] / "storage" / "repositories"


class RepositoryNotFoundError(Exception):
    pass


class CloneFailedError(Exception):
    pass


class ProviderNotSupportedError(Exception):
    pass


class RepositoryImportService:
    def import_from_url(self, provider: str, remote_url: str, workspace_id: str) -> Repository:
        provider_value = self._normalize_provider(provider)
        repo = Repository(provider=provider_value, workspace_id=workspace_id, remote_url=remote_url)
        REPOSITORY_STORE.set(repo)
        try:
            if provider_value in {Provider.GITHUB, Provider.GITLAB, Provider.BITBUCKET}:
                self._clone(repo)
            else:
                self._mark_placeholder(repo)
        except CloneFailedError:
            repo.status = RepositoryStatus.IMPORTING
            repo.updated_at = datetime.now(timezone.utc)
            REPOSITORY_STORE.set(repo)
        return repo

    def list_repositories(self) -> List[Repository]:
        return list(REPOSITORY_STORE.values())

    def get_repository(self, repository_id: str) -> Repository:
        repo = REPOSITORY_STORE.get(repository_id)
        if repo is None:
            raise RepositoryNotFoundError(repository_id)
        return repo

    def delete_repository(self, repository_id: str) -> DeleteRepositoryResponse:
        repo = self.get_repository(repository_id)
        repo.status = RepositoryStatus.DELETED
        repo.updated_at = datetime.now(timezone.utc)
        REPOSITORY_STORE.set(repo)
        REPOSITORY_STORE.pop(repository_id)
        return DeleteRepositoryResponse(id=repo.id, status=repo.status.value)

    def to_response(self, repo: Repository) -> RepositoryResponse:
        return RepositoryResponse(
            id=repo.id,
            provider=repo.provider.value,
            workspace_id=repo.workspace_id,
            remote_url=repo.remote_url,
            storage_path=repo.storage_path,
            default_branch=repo.default_branch,
            current_branch=repo.current_branch,
            commit_sha=repo.commit_sha,
            file_count=repo.file_count,
            total_bytes=repo.total_bytes,
            status=repo.status.value,
            created_at=repo.created_at.isoformat() + "Z",
            updated_at=repo.updated_at.isoformat() + "Z",
        )

    def _normalize_provider(self, provider: str) -> Provider:
        try:
            return Provider(provider.lower())
        except ValueError as exc:
            raise ProviderNotSupportedError(provider) from exc

    def _clone(self, repo: Repository) -> None:
        target = STORAGE_ROOT / repo.id / "source"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo.remote_url, str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
            branch = subprocess.run(
                ["git", "-C", str(target), "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            commit_sha = subprocess.run(
                ["git", "-C", str(target), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            file_count, total_bytes = self._scan(target)
            repo.mark_ready(
                storage_path=str(target),
                default_branch=branch,
                commit_sha=commit_sha,
                file_count=file_count,
                total_bytes=total_bytes,
            )
            REPOSITORY_STORE.set(repo)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            repo.mark_failed()
            raise CloneFailedError(str(exc)) from exc

    def _mark_placeholder(self, repo: Repository) -> None:
        repo.mark_ready(storage_path=str(STORAGE_ROOT / repo.id / "source"), file_count=0, total_bytes=0)
        REPOSITORY_STORE.set(repo)

    def _scan(self, path: Path):
        file_count = 0
        total_bytes = 0
        for root, _, files in os.walk(path):
            for name in files:
                file_count += 1
                total_bytes += (Path(root) / name).stat().st_size
        return file_count, total_bytes
