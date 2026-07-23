"""FastAPI router for AST Parser module."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.ast_parser.exceptions import (
    ASTParserException,
    RepositoryNotFoundException,
    RepositoryNotReadyException,
    TechnologyDetectionNotFoundException,
)
from app.modules.ast_parser.schemas import ASTParseRequest, ASTParseResponse
from app.modules.ast_parser.service import ASTParserService

router = APIRouter(prefix="/api/v1/ast-parser", tags=["ast-parser"])


def get_ast_parser_service() -> ASTParserService:
    """Dependency provider for ASTParserService instance."""
    return ASTParserService()


@router.post(
    "/start",
    response_model=ASTParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare repository for AST parsing",
    description=(
        "Validates repository existence, status, technology detection output, "
        "and prepares parsing context for supported programming languages."
    ),
)
def start_ast_parsing(
    payload: ASTParseRequest,
    service: Annotated[ASTParserService, Depends(get_ast_parser_service)],
) -> ASTParseResponse:
    """Prepare repository metadata and context for AST parsing.

    Args:
        payload: ASTParseRequest containing target repository_id UUID.
        service: ASTParserService dependency instance.

    Returns:
        ASTParseResponse summary containing supported/unsupported languages and file counts.

    Raises:
        HTTPException 404: If repository or technology detection analysis is missing.
        HTTPException 400: If repository is not ready for parsing.
    """
    try:
        response = service.start_parsing_prep(repository_id=payload.repository_id)
        print("Response: ", response)
        return response
    except RepositoryNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REPOSITORY_NOT_FOUND",
                "message": exc.message,
                "repository_id": exc.repository_id,
            },
        ) from exc
    except TechnologyDetectionNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TECHNOLOGY_DETECTION_NOT_FOUND",
                "message": exc.message,
                "repository_id": exc.repository_id,
            },
        ) from exc
    except RepositoryNotReadyException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REPOSITORY_NOT_READY",
                "message": exc.message,
                "repository_id": exc.repository_id,
                "status": exc.status,
            },
        ) from exc
    except ASTParserException as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "AST_PARSER_ERROR",
                "message": exc.message,
            },
        ) from exc
