import subprocess
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.repository.models import REPOSITORY_STORE
from app.modules.repository.service import RepositoryImportService
from main import app

client = TestClient(app)


def _create_local_git_repo() -> Path:
    temp_dir = tempfile.mkdtemp(prefix="repo-test-")
    repo_path = Path(temp_dir)
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True, text=True)
    (repo_path / "README.md").write_text("demo repository", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_path, check=True, capture_output=True, text=True)
    return repo_path


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_import_repository_endpoint():
    repo_path = _create_local_git_repo()
    response = client.post(
        "/v1/repositories",
        json={
            "provider": "github",
            "remote_url": str(repo_path),
            "workspace_id": "workspace-123",
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ready"

    stored_repo = REPOSITORY_STORE.get(payload["id"])
    assert stored_repo is not None
    assert stored_repo.status.value == "ready"
    assert Path(stored_repo.storage_path).name == "source"


def test_analyze_repository_endpoint():
    repo_path = _create_local_git_repo()
    response = client.post(
        "/v1/repositories",
        json={
            "provider": "github",
            "remote_url": str(repo_path),
            "workspace_id": "workspace-123",
        },
    )
    repo_id = response.json()["data"]["id"]

    analyze_response = client.post(f"/v1/repositories/{repo_id}/analyze")
    assert analyze_response.status_code == 200
    payload = analyze_response.json()["data"]
    assert payload["repository_id"] == repo_id
    assert payload["summary"]["total_files"] > 0
    assert payload["detected_languages"]


def test_list_and_get_repository_endpoint():
    response = client.get("/v1/repositories")
    assert response.status_code == 200
    repositories = response.json()["data"]
    assert isinstance(repositories, list)
    assert repositories

    repo_id = repositories[0]["id"]
    detail_response = client.get(f"/v1/repositories/{repo_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == repo_id


def test_repository_persists_across_service_instances():
    REPOSITORY_STORE.clear()

    service = RepositoryImportService()
    repo = service.import_from_url(
        provider="github",
        remote_url="https://github.com/example/repo.git",
        workspace_id="workspace-123",
    )

    next_service = RepositoryImportService()
    reloaded = next_service.get_repository(repo.id)

    assert reloaded.id == repo.id
    assert reloaded.workspace_id == "workspace-123"
