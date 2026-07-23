"""Tree-sitter parser placeholders for future iteration."""

from typing import Any, Union


def load_language(language: str) -> Any:
    """Load Tree-sitter language grammar object.

    Args:
        language: Canonical language identifier.

    Raises:
        NotImplementedError: Tree-sitter module integration is pending next iteration.
    """
    raise NotImplementedError(
        f"Tree-sitter language loader for '{language}' is not implemented yet."
    )


def load_query(language: str, query_name: str) -> Any:
    """Load Tree-sitter query string for a language.

    Args:
        language: Canonical language identifier.
        query_name: Name of query file (e.g. "symbols", "imports").

    Raises:
        NotImplementedError: Tree-sitter query loader is not implemented yet.
    """
    raise NotImplementedError(
        f"Tree-sitter query loader for '{language}:{query_name}' is not implemented yet."
    )


def parse_source(source_code: Union[str, bytes], language: str) -> Any:
    """Parse source code string into a Tree-sitter syntax tree.

    Args:
        source_code: Raw source code string or bytes.
        language: Canonical language identifier.

    Raises:
        NotImplementedError: Tree-sitter source parser is not implemented yet.
    """
    raise NotImplementedError(
        f"Tree-sitter parser for '{language}' source code is not implemented yet."
    )
