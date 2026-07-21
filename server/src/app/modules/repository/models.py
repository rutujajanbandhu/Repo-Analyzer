import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class Provider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"
    ZIP = "zip"
    PASTE = "paste"


class RepositoryStatus(str, Enum):
    IMPORTING = "importing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Repository:
    """Plain in-memory representation of a repository row.
    No database yet - persistence will be added later (see A.7 storage ownership).
    """

    def __init__(
        self,
        provider: Provider,
        workspace_id: str,
        remote_url: Optional[str] = None,
    ):
        self.id: str = str(uuid.uuid4())
        self.provider: Provider = provider
        self.workspace_id: str = workspace_id
        self.remote_url: Optional[str] = remote_url
        self.storage_path: Optional[str] = None
        self.default_branch: Optional[str] = None
        self.current_branch: Optional[str] = None
        self.commit_sha: Optional[str] = None
        self.file_count: int = 0
        self.total_bytes: int = 0
        self.status: RepositoryStatus = RepositoryStatus.IMPORTING
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

    def mark_ready(self, **fields) -> None:
        for key, value in fields.items():
            setattr(self, key, value)
        self.status = RepositoryStatus.READY
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self) -> None:
        self.status = RepositoryStatus.FAILED
        self.updated_at = datetime.now(timezone.utc)


DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "storage" / "repositories"
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORE_FILE = DATA_DIR / "repositories.json"


class RepositoryStore:
    def __init__(self) -> None:
        self._data: Dict[str, Repository] = {}
        self._load()

    def _load(self) -> None:
        if not STORE_FILE.exists():
            return
        try:
            payload = json.loads(STORE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return

        for repo_id, repo_data in payload.items():
            repo = Repository(
                provider=Provider(repo_data["provider"]),
                workspace_id=repo_data["workspace_id"],
                remote_url=repo_data.get("remote_url"),
            )
            repo.id = repo_id
            repo.storage_path = repo_data.get("storage_path")
            repo.default_branch = repo_data.get("default_branch")
            repo.current_branch = repo_data.get("current_branch")
            repo.commit_sha = repo_data.get("commit_sha")
            repo.file_count = repo_data.get("file_count", 0)
            repo.total_bytes = repo_data.get("total_bytes", 0)
            repo.status = RepositoryStatus(repo_data.get("status", RepositoryStatus.IMPORTING.value))
            repo.created_at = datetime.fromisoformat(repo_data["created_at"])
            repo.updated_at = datetime.fromisoformat(repo_data["updated_at"])
            self._data[repo_id] = repo

    def _save(self) -> None:
        payload = {}
        for repo_id, repo in self._data.items():
            payload[repo_id] = {
                "provider": repo.provider.value,
                "workspace_id": repo.workspace_id,
                "remote_url": repo.remote_url,
                "storage_path": repo.storage_path,
                "default_branch": repo.default_branch,
                "current_branch": repo.current_branch,
                "commit_sha": repo.commit_sha,
                "file_count": repo.file_count,
                "total_bytes": repo.total_bytes,
                "status": repo.status.value,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
            }
        STORE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, repository_id: str) -> Optional[Repository]:
        return self._data.get(repository_id)

    def set(self, repo: Repository) -> None:
        self._data[repo.id] = repo
        self._save()

    def values(self):
        return self._data.values()

    def pop(self, repository_id: str) -> Optional[Repository]:
        repo = self._data.pop(repository_id, None)
        self._save()
        return repo

    def clear(self) -> None:
        self._data.clear()
        self._save()


REPOSITORY_STORE = RepositoryStore()