"""Constants for the AST Parser module."""

from pathlib import Path
from typing import Final, Mapping

# Base directory for storage relative to current module location
_SERVER_SRC_DIR: Final[Path] = Path(__file__).resolve().parents[3]

DEFAULT_STORAGE_FOLDER: Final[Path] = _SERVER_SRC_DIR / "storage" / "repositories"
DEFAULT_AST_FOLDER: Final[Path] = _SERVER_SRC_DIR / "storage" / "ast_output"

MAX_FILE_SIZE_MB: Final[int] = 10

SUPPORTED_LANGUAGES: Final[tuple[str, ...]] = (
    "python",
    "javascript",
    "typescript",
    "java",
    "go",
    "rust",
    "c",
    "cpp",
    "php",
)

LANGUAGE_ALIASES: Final[Mapping[str, str]] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "node": "javascript",
    "c++": "cpp",
    "cxx": "cpp",
    "cc": "cpp",
    "h": "c",
    "hpp": "cpp",
}

LANGUAGE_EXTENSIONS: Final[Mapping[str, tuple[str, ...]]] = {
    "python": (".py", ".pyw"),
    "javascript": (".js", ".jsx", ".mjs", ".cjs"),
    "typescript": (".ts", ".tsx"),
    "java": (".java",),
    "go": (".go",),
    "rust": (".rs",),
    "c": (".c", ".h"),
    "cpp": (".cpp", ".hpp", ".cc", ".cxx", ".hh"),
    "php": (".php",),
}
