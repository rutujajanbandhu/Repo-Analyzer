"""Filesystem utilities for AST Parser module."""

import json
from pathlib import Path
from typing import Any, Dict, Union


def file_exists(path: Union[str, Path]) -> bool:
    """Check if a file or directory exists at the given path.

    Args:
        path: Path string or Path object to check.

    Returns:
        True if path exists, False otherwise.
    """
    target = Path(path)
    return target.exists()


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Read and parse JSON content from a file path.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON dictionary content.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If content is invalid JSON.
    """
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"JSON file not found at path: {target}")

    with open(target, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
        return data


def save_json(path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """Write data dictionary to a file in formatted JSON format.

    Args:
        path: Target file path.
        data: Dictionary data to write.
        indent: JSON indentation spaces.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory path exists, creating parents if necessary.

    Args:
        path: Directory path string or Path object.

    Returns:
        Path object pointing to the directory.
    """
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def repository_exists(storage_dir: Union[str, Path], repository_id: str) -> bool:
    """Verify if a repository JSON entry or directory exists in storage.

    Args:
        storage_dir: Root storage directory containing repositories.json or repo folders.
        repository_id: Repository UUID identifier.

    Returns:
        True if repository exists, False otherwise.
    """
    storage_path = Path(storage_dir)
    json_path = storage_path / "repositories.json"

    if json_path.exists():
        try:
            data = load_json(json_path)
            if repository_id in data:
                return True
        except Exception:
            pass

    repo_folder = storage_path / repository_id
    return repo_folder.exists() and repo_folder.is_dir()
