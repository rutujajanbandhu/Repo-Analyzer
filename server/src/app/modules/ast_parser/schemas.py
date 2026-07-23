"""Pydantic v2 schemas for AST Parser module."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.ast_parser.enums import LanguageSupportStatus, RepositoryStatus


class ASTParseRequest(BaseModel):
    """Request payload to prepare repository AST parsing."""

    model_config = ConfigDict(extra="forbid")

    repository_id: str = Field(
        ...,
        description="Unique UUID identifier of the target repository.",
        examples=["94e818a2-7976-4c6e-8389-38f598232a6b"],
    )


class ASTParseResponse(BaseModel):
    """Response payload summarizing repository AST parsing readiness."""

    model_config = ConfigDict(from_attributes=True)

    repository_id: str = Field(..., description="Repository UUID.")
    status: RepositoryStatus = Field(..., description="Repository status.")
    repository_path: str = Field(..., description="Absolute filesystem path to source directory.")
    languages: List[str] = Field(
        default_factory=list, description="All detected languages in repository."
    )
    supported_languages: List[str] = Field(
        default_factory=list, description="Languages supported for AST parsing."
    )
    unsupported_languages: List[str] = Field(
        default_factory=list, description="Detected languages not supported for AST parsing."
    )
    total_supported_files: int = Field(
        ..., ge=0, description="Total count of files matching supported languages."
    )
    total_files: int = Field(..., ge=0, description="Total file count across all languages.")


class LanguageSummary(BaseModel):
    """Detailed summary of detected language file counts and support status."""

    language: str = Field(..., description="Normalized language name.")
    count: int = Field(..., ge=0, description="Number of detected files for language.")
    support_status: LanguageSupportStatus = Field(
        ..., description="Whether language is supported for AST parsing."
    )


class ParsingContext(BaseModel):
    """Execution context prepared for downstream AST parsing engine."""

    repository_id: str = Field(..., description="Repository UUID.")
    repository_path: str = Field(..., description="Absolute storage path to source files.")
    status: RepositoryStatus = Field(..., description="Current repository status.")
    languages: List[str] = Field(default_factory=list, description="All detected languages.")
    supported_languages: List[str] = Field(
        default_factory=list, description="List of supported languages."
    )
    unsupported_languages: List[str] = Field(
        default_factory=list, description="List of unsupported languages."
    )
    total_supported_files: int = Field(
        ..., ge=0, description="Total count of supported source files."
    )
    total_files: int = Field(..., ge=0, description="Total count of all files.")
    detected_languages: Dict[str, int] = Field(
        default_factory=dict, description="Raw detected language file counts."
    )
    file_groups: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Relative file paths grouped by normalized language name.",
    )
    frameworks: List[str] = Field(
        default_factory=list, description="Frameworks detected in repository analysis."
    )
    entry_points: List[str] = Field(default_factory=list, description="Detected entry point paths.")

    def to_response(self) -> ASTParseResponse:
        """Convert parsing context into standard API response schema."""
        return ASTParseResponse(
            repository_id=self.repository_id,
            status=self.status,
            repository_path=self.repository_path,
            languages=self.languages,
            supported_languages=self.supported_languages,
            unsupported_languages=self.unsupported_languages,
            total_supported_files=self.total_supported_files,
            total_files=self.total_files,
        )


class TechnologyAnalysisSummary(BaseModel):
    """Summary subsection inside technology detection metadata."""

    total_files: int = Field(0, ge=0)
    total_bytes: int = Field(0, ge=0)
    root_directory: Optional[str] = Field(None)


class TechnologyAnalysisInfo(BaseModel):
    """Technology detection output structure inside repository JSON metadata."""

    repository_id: str
    status: Optional[str] = Field(None)
    summary: Optional[TechnologyAnalysisSummary] = Field(None)
    detected_languages: Dict[str, int] = Field(default_factory=dict)
    frameworks: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    top_level_directories: List[str] = Field(default_factory=list)
    notable_files: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)


class RepositoryInfo(BaseModel):
    """Metadata representation of a repository in local JSON storage."""

    provider: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None)
    remote_url: Optional[str] = Field(None)
    storage_path: str
    default_branch: Optional[str] = Field(None)
    current_branch: Optional[str] = Field(None)
    commit_sha: Optional[str] = Field(None)
    file_count: Optional[int] = Field(0)
    total_bytes: Optional[int] = Field(0)
    status: RepositoryStatus
    analysis: Optional[TechnologyAnalysisInfo] = Field(None)
    created_at: Optional[str] = Field(None)
    updated_at: Optional[str] = Field(None)
