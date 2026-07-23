import sys
from pathlib import Path

# Ensure src directory is in sys.path
src_dir = str(Path(__file__).resolve().parents[1] / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.modules.ast_parser.enums import RepositoryStatus  # noqa: E402
from app.modules.ast_parser.exceptions import (  # noqa: E402
    RepositoryNotFoundException,
    RepositoryNotReadyException,
    TechnologyDetectionNotFoundException,
)
from app.modules.ast_parser.service import ASTParserService  # noqa: E402
from app.modules.ast_parser.utils.filesystem import (  # noqa: E402
    ensure_directory,
    file_exists,
    load_json,
    repository_exists,
    save_json,
)
from app.modules.ast_parser.utils.hash import sha256_file, sha256_string  # noqa: E402
from app.modules.ast_parser.utils.language_loader import (  # noqa: E402
    get_extensions_for_language,
    get_language_for_extension,
    is_supported,
    normalize_language,
)
from app.modules.ast_parser.utils.tree_utils import (  # noqa: E402
    load_language,
    load_query,
    parse_source,
)

from main import app  # noqa: E402

client = TestClient(app)


EXISTING_REPO_ID = "94e818a2-7976-4c6e-8389-38f598232a6b"


def test_language_loader_utilities():
    """Test language normalization, detection, and extension mappings."""
    assert normalize_language("JavaScript") == "javascript"
    assert normalize_language("js") == "javascript"
    assert normalize_language("Py") == "python"
    assert normalize_language("C++") == "cpp"

    assert is_supported("python") is True
    assert is_supported("javascript") is True
    assert is_supported("go") is True
    assert is_supported("markdown") is False
    assert is_supported("json") is False

    assert ".py" in get_extensions_for_language("python")
    assert get_language_for_extension("index.js") == "javascript"
    assert get_language_for_extension("main.go") == "go"
    assert get_language_for_extension("readme.md") is None


def test_hash_utilities(tmp_path: Path):
    """Test sha256 hashing helper functions."""
    assert len(sha256_string("hello world")) == 64

    test_file = tmp_path / "test.txt"
    test_file.write_text("sample content", encoding="utf-8")
    file_hash = sha256_file(test_file)
    assert file_hash == sha256_string("sample content")


def test_filesystem_utilities(tmp_path: Path):
    """Test filesystem helper functions."""
    d = ensure_directory(tmp_path / "nested" / "dir")
    assert d.exists() and d.is_dir()

    f = d / "data.json"
    save_json(f, {"key": "value"})
    assert file_exists(f) is True

    loaded = load_json(f)
    assert loaded == {"key": "value"}

    assert repository_exists(tmp_path, "non-existent") is False


def test_tree_utils_placeholders():
    """Test tree_utils functions raise NotImplementedError."""
    with pytest.raises(NotImplementedError):
        load_language("python")

    with pytest.raises(NotImplementedError):
        load_query("python", "symbols")

    with pytest.raises(NotImplementedError):
        parse_source("print('hello')", "python")


def test_ast_parser_service_existing_repo():
    """Test ASTParserService with the existing pre-populated repository."""
    service = ASTParserService()
    context = service.prepare_parsing_context(EXISTING_REPO_ID)

    assert context.repository_id == EXISTING_REPO_ID
    assert context.status == RepositoryStatus.READY
    assert "javascript" in context.supported_languages
    assert "markdown" in context.unsupported_languages
    assert context.total_supported_files == 31
    assert context.total_files == 55

    response = service.start_parsing_prep(EXISTING_REPO_ID)
    assert response.repository_id == EXISTING_REPO_ID
    assert response.status == RepositoryStatus.READY
    assert response.supported_languages == ["javascript"]
    assert "markdown" in response.unsupported_languages


def test_ast_parser_service_missing_repo():
    """Test ASTParserService throws RepositoryNotFoundException for unknown ID."""
    service = ASTParserService()
    with pytest.raises(RepositoryNotFoundException):
        service.prepare_parsing_context("00000000-0000-0000-0000-000000000000")


def test_ast_parser_service_unready_repo(tmp_path: Path):
    """Test ASTParserService throws RepositoryNotReadyException when status is processing."""
    repos = {
        "unready-id": {
            "status": "processing",
            "storage_path": str(tmp_path),
            "analysis": {"detected_languages": {"python": 10}},
        }
    }
    save_json(tmp_path / "repositories.json", repos)
    service = ASTParserService(storage_dir=tmp_path)

    with pytest.raises(RepositoryNotReadyException) as exc_info:
        service.prepare_parsing_context("unready-id")

    assert exc_info.value.status == "processing"


def test_ast_parser_service_missing_analysis(tmp_path: Path):
    """Test ASTParserService throws TechnologyDetectionNotFoundException when analysis is missing."""
    repos = {
        "no-analysis-id": {
            "status": "ready",
            "storage_path": str(tmp_path),
        }
    }
    save_json(tmp_path / "repositories.json", repos)
    service = ASTParserService(storage_dir=tmp_path)

    with pytest.raises(TechnologyDetectionNotFoundException):
        service.prepare_parsing_context("no-analysis-id")


def test_api_start_parsing_success():
    """Test POST /api/v1/ast-parser/start endpoint with existing repository."""
    response = client.post(
        "/api/v1/ast-parser/start",
        json={"repository_id": EXISTING_REPO_ID},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["repository_id"] == EXISTING_REPO_ID
    assert data["status"] == "ready"
    assert data["supported_languages"] == ["javascript"]
    assert "markdown" in data["unsupported_languages"]
    assert data["total_supported_files"] == 31
    assert data["total_files"] == 55


def test_api_start_parsing_missing_repo():
    """Test POST /api/v1/ast-parser/start endpoint with missing repository ID."""
    response = client.post(
        "/api/v1/ast-parser/start",
        json={"repository_id": "non-existent-uuid"},
    )
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "REPOSITORY_NOT_FOUND"
