import json
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

    def list_repositories_for_workspace(self, workspace_id: str) -> List[Repository]:
        return [repo for repo in REPOSITORY_STORE.values() if repo.workspace_id == workspace_id]

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

    def analyze_repository(self, repository_id: str) -> dict:
        repo = self.get_repository(repository_id)
        if repo.storage_path is None:
            analysis = {
                "repository_id": repo.id,
                "status": repo.status.value,
                "summary": {"total_files": 0, "total_bytes": 0, "root_directory": None},
                "detected_languages": {},
                "frameworks": [],
                "entry_points": [],
                "top_level_directories": [],
                "notable_files": [],
                "insights": ["No repository content is available yet."],
            }
            repo.analysis = analysis
            REPOSITORY_STORE.set(repo)
            return analysis

        root = Path(repo.storage_path)
        if not root.exists():
            raise FileNotFoundError(f"Repository storage path not found: {repo.storage_path}")

        languages = {}
        frameworks = set()
        entry_points = []
        notable_files = []
        total_files = 0
        total_bytes = 0
        top_level_directories = []

        skip_dirs = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "dist", "build", "target", "__pycache__", "vendor", ".pytest_cache", ".mypy_cache", ".idea"}

        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
            if current_root == str(root):
                top_level_directories = [d for d in sorted(dirnames) if not d.startswith(".")][:10]
            for filename in sorted(filenames):
                if filename.startswith(".") and filename not in {".env.example"}:
                    continue
                file_path = Path(current_root) / filename
                rel_path = file_path.relative_to(root).as_posix()
                total_files += 1
                total_bytes += file_path.stat().st_size

                suffix = file_path.suffix.lower()
                ext_map = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".tsx": "typescript",
                    ".jsx": "javascript",
                    ".go": "go",
                    ".java": "java",
                    ".cs": "csharp",
                    ".rb": "ruby",
                    ".php": "php",
                    ".rs": "rust",
                    ".swift": "swift",
                    ".kt": "kotlin",
                    ".scala": "scala",
                    ".cpp": "cpp",
                    ".c": "c",
                    ".h": "c",
                    ".hpp": "cpp",
                    ".sh": "shell",
                    ".ps1": "powershell",
                    ".sql": "sql",
                    ".md": "markdown",
                    ".yml": "yaml",
                    ".yaml": "yaml",
                    ".json": "json",
                    ".toml": "toml",
                    ".ini": "ini",
                    ".cfg": "cfg",
                }
                if suffix in ext_map:
                    lang = ext_map[suffix]
                    languages[lang] = languages.get(lang, 0) + 1

                base_name = filename.lower()
                if base_name in {"readme.md", "pyproject.toml", "requirements.txt", "package.json", "dockerfile", "docker-compose.yml", "compose.yaml", "setup.py", "manage.py", "main.py", "app.py", "server.py", "index.js", "index.ts", "tsconfig.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"}:
                    notable_files.append(rel_path)

                if base_name in {"main.py", "app.py", "server.py", "manage.py", "index.js", "index.ts", "main.js", "main.ts", "server.ts"} or rel_path.endswith(("/main.py", "/app.py", "/server.py", "/manage.py", "/index.js", "/index.ts", "/main.js", "/main.ts")):
                    entry_points.append(rel_path)

                if base_name in {"package.json", "pyproject.toml", "requirements.txt", "setup.py", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"}:
                    try:
                        text = file_path.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        text = ""
                    if base_name == "package.json":
                        try:
                            payload = json.loads(text)
                        except json.JSONDecodeError:
                            payload = {}
                        for name in list(payload.get("dependencies", {}).keys()) + list(payload.get("devDependencies", {}).keys()):
                            if name in {"react", "next", "express", "fastify", "nestjs", "vue"}:
                                frameworks.add(name)
                    for token in ["fastapi", "flask", "django", "pytest", "pydantic", "express", "react", "next", "nestjs"]:
                        if token in text.lower():
                            frameworks.add(token)

        analysis = {
            "repository_id": repo.id,
            "status": repo.status.value,
            "summary": {
                "total_files": total_files,
                "total_bytes": total_bytes,
                "root_directory": root.name,
            },
            "detected_languages": dict(sorted(languages.items())),
            "frameworks": sorted(frameworks),
            "entry_points": sorted(entry_points),
            "top_level_directories": top_level_directories,
            "notable_files": sorted(notable_files),
            "insights": [
                f"Detected {total_files} file(s) and {len(languages)} language family(ies).",
                f"Entry points: {', '.join(entry_points) if entry_points else 'none detected' }.",
                f"Framework hints: {', '.join(sorted(frameworks)) if frameworks else 'none detected' }.",
            ],
        }
        repo.analysis = analysis
        REPOSITORY_STORE.set(repo)
        return analysis

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
