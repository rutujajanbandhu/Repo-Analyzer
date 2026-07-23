"""Cryptographic hashing utilities for AST Parser module."""

import hashlib
from pathlib import Path
from typing import Union


def sha256_file(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Calculate hex-encoded SHA-256 hash of a file on disk.

    Args:
        file_path: Target file path.
        chunk_size: Read buffer size in bytes.

    Returns:
        SHA-256 digest string in lowercase hexadecimal format.
    """
    path = Path(file_path)
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_string(content: str) -> str:
    """Calculate hex-encoded SHA-256 hash of a string.

    Args:
        content: Input string content.

    Returns:
        SHA-256 digest string in lowercase hexadecimal format.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
