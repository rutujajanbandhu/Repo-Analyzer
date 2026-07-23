"""Enumerations for AST Parser module."""

from enum import Enum


class RepositoryStatus(str, Enum):
    """Status of repository analysis readiness."""

    READY = "ready"
    FAILED = "failed"
    PROCESSING = "processing"


class LanguageSupportStatus(str, Enum):
    """Support status for programming languages in Tree-sitter parsing."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
