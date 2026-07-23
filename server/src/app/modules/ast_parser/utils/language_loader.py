"""Language detection and normalization utilities for AST Parser module."""

from typing import Optional, Sequence

from app.modules.ast_parser.constants import (
    LANGUAGE_ALIASES,
    LANGUAGE_EXTENSIONS,
    SUPPORTED_LANGUAGES,
)


def normalize_language(language: str) -> str:
    """Normalize raw language string to standard canonical representation.

    Args:
        language: Raw language name (e.g. "JavaScript", "js", "C++", "Py").

    Returns:
        Canonical lowercase language identifier string.
    """
    cleaned = language.strip().lower()
    return LANGUAGE_ALIASES.get(cleaned, cleaned)


def is_supported(language: str) -> bool:
    """Determine whether a given language is supported for AST parsing.

    Args:
        language: Raw or normalized language name.

    Returns:
        True if language is supported, False otherwise.
    """
    normalized = normalize_language(language)
    return normalized in SUPPORTED_LANGUAGES


def get_extensions_for_language(language: str) -> Sequence[str]:
    """Retrieve file extensions associated with a programming language.

    Args:
        language: Raw or normalized language name.

    Returns:
        Sequence of file extensions (e.g. (".py", ".pyw")).
    """
    normalized = normalize_language(language)
    return LANGUAGE_EXTENSIONS.get(normalized, ())


def get_language_for_extension(file_path_or_extension: str) -> Optional[str]:
    """Identify matching normalized language for a file path or extension.

    Args:
        file_path_or_extension: File path string or file extension (e.g. ".js").

    Returns:
        Normalized language string if matched, None otherwise.
    """
    ext = file_path_or_extension.lower()
    if "." in ext:
        ext = "." + ext.rsplit(".", 1)[-1]

    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None
