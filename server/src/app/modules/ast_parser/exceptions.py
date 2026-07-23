"""Custom domain exceptions for AST Parser module."""


class ASTParserException(Exception):
    """Base exception for all AST Parser errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RepositoryNotFoundException(ASTParserException):
    """Raised when the specified repository ID is missing from storage."""

    def __init__(self, repository_id: str) -> None:
        message = f"Repository with ID '{repository_id}' was not found in storage."
        super().__init__(message)
        self.repository_id = repository_id


class RepositoryNotReadyException(ASTParserException):
    """Raised when repository analysis status is not ready."""

    def __init__(self, repository_id: str, status: str) -> None:
        message = (
            f"Repository '{repository_id}' is not ready for AST parsing. "
            f"Current status: '{status}'."
        )
        super().__init__(message)
        self.repository_id = repository_id
        self.status = status


class TechnologyDetectionNotFoundException(ASTParserException):
    """Raised when technology detection analysis output is missing for a repository."""

    def __init__(self, repository_id: str) -> None:
        message = f"Technology detection analysis outputs were not found for repository '{repository_id}'."
        super().__init__(message)
        self.repository_id = repository_id


class UnsupportedLanguageException(ASTParserException):
    """Raised when an operation requires a supported language but an unsupported language was provided."""

    def __init__(self, language: str) -> None:
        message = f"Language '{language}' is not supported for AST parsing."
        super().__init__(message)
        self.language = language
