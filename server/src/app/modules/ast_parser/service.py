"""Business logic service layer for AST Parser module."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from app.modules.ast_parser.constants import DEFAULT_STORAGE_FOLDER
from app.modules.ast_parser.enums import RepositoryStatus
from app.modules.ast_parser.exceptions import (
    RepositoryNotFoundException,
    RepositoryNotReadyException,
    TechnologyDetectionNotFoundException,
)
from app.modules.ast_parser.schemas import ASTParseResponse, ParsingContext

from app.modules.ast_parser.utils.filesystem import file_exists, load_json
from app.modules.ast_parser.utils.language_loader import (
    get_language_for_extension,
    is_supported,
    normalize_language,
)

logger = logging.getLogger(__name__)


class ASTParserService:
    """Service handling repository validation, context preparation, and parsing summary."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None) -> None:
        """Initialize ASTParserService with root storage folder location.

        Args:
            storage_dir: Root storage path containing repositories.json metadata.
        """
        self.storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_FOLDER

    def prepare_parsing_context(self, repository_id: str) -> ParsingContext:
        """Prepare repository AST parsing context by validating metadata and structure.

        Args:
            repository_id: Unique UUID identifier of target repository.

        Returns:
            ParsingContext object ready for AST parsing workers.

        Raises:
            RepositoryNotFoundException: If repository entry or storage path missing.
            RepositoryNotReadyException: If repository analysis status is not ready.
            TechnologyDetectionNotFoundException: If technology analysis is missing.
        """
        logger.info("Preparing parsing context for repository: %s", repository_id)

        # 1 & 2. Load repository JSON and find entry
        repo_data = self._load_repository_entry(repository_id)
        print("Repo Data: ", repo_data)

        # 3 & 4. Verify repository status
        raw_status = repo_data.get("status", "")
        if raw_status.lower() != RepositoryStatus.READY.value:
            logger.warning(
                "Repository %s status is '%s', expected 'ready'", repository_id, raw_status
            )
            raise RepositoryNotReadyException(repository_id=repository_id, status=raw_status)

        # 5. Read analysis section
        analysis = repo_data.get("analysis")
        if not analysis or not isinstance(analysis, dict):
            logger.error("Analysis data missing for repository %s", repository_id)
            raise TechnologyDetectionNotFoundException(repository_id=repository_id)

        # Validate storage path
        raw_storage_path = repo_data.get("storage_path", "")
        repo_path = (
            Path(raw_storage_path)
            if raw_storage_path
            else self.storage_dir / repository_id / "source"
        )
        if not file_exists(repo_path):
            logger.error("Repository storage path does not exist: %s", repo_path)
            raise RepositoryNotFoundException(repository_id=repository_id)

        # 6. Determine supported vs unsupported languages
        detected_langs_raw: Dict[str, int] = analysis.get("detected_languages", {})
        all_langs, supported_langs, unsupported_langs = self._classify_languages(detected_langs_raw)

        # 7. Scan repository and group files by supported language
        file_groups, scanned_counts = self._group_files_by_language(repo_path)

        # 8. Compute total counts
        total_supported = sum(scanned_counts.get(lang, 0) for lang in supported_langs)
        if total_supported == 0 and supported_langs:
            # Fallback to technology detection counts if scan finds no files
            total_supported = sum(detected_langs_raw.get(lang, 0) for lang in supported_langs)

        total_files = analysis.get("summary", {}).get("total_files") or sum(
            detected_langs_raw.values()
        )
        if total_files == 0:
            total_files = sum(len(files) for files in file_groups.values())

        frameworks = analysis.get("frameworks", [])
        entry_points = analysis.get("entry_points", [])

        context = ParsingContext(
            repository_id=repository_id,
            repository_path=str(repo_path.resolve()),
            status=RepositoryStatus.READY,
            languages=all_langs,
            supported_languages=supported_langs,
            unsupported_languages=unsupported_langs,
            total_supported_files=total_supported,
            total_files=total_files,
            detected_languages=detected_langs_raw,
            file_groups=file_groups,
            frameworks=frameworks,
            entry_points=entry_points,
        )

        logger.info(
            "Successfully built parsing context for repo %s. Supported files: %d / %d",
            repository_id,
            total_supported,
            total_files,
        )
        return context

    def start_parsing_prep(self, repository_id: str) -> ASTParseResponse:
        """API wrapper method to process request and return response model.

        Args:
            repository_id: Unique UUID identifier of target repository.

        Returns:
            ASTParseResponse response model.
        """
        context = self.prepare_parsing_context(repository_id)
        print("Context: ", context)
        return context.to_response()

    def _load_repository_entry(self, repository_id: str) -> Dict:
        """Load repository entry dictionary from repositories.json storage file.

        Args:
            repository_id: Unique UUID identifier.

        Returns:
            Raw repository metadata dictionary.

        Raises:
            RepositoryNotFoundException: If repositories.json is missing or key not found.
        """
        json_path = self.storage_dir / "repositories.json"
        if not file_exists(json_path):
            logger.error("Repositories index file missing at %s", json_path)
            raise RepositoryNotFoundException(repository_id=repository_id)

        try:
            repositories = load_json(json_path)
            print("Repositories: ", repositories)
        except Exception as exc:
            logger.error("Failed to load repositories JSON: %s", exc)
            raise RepositoryNotFoundException(repository_id=repository_id) from exc

        if repository_id not in repositories:
            logger.warning("Repository ID %s not found in repositories.json", repository_id)
            raise RepositoryNotFoundException(repository_id=repository_id)

        return repositories[repository_id]

    def _classify_languages(
        self, detected_languages: Dict[str, int]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Classify raw detected languages into canonical supported and unsupported lists.

        Args:
            detected_languages: Mapping of language names to file counts.

        Returns:
            Tuple of (all_languages, supported_languages, unsupported_languages).
        """
        all_langs: List[str] = []
        supported_langs: List[str] = []
        unsupported_langs: List[str] = []

        for raw_lang in detected_languages.keys():
            normalized = normalize_language(raw_lang)
            if normalized not in all_langs:
                all_langs.append(normalized)

            if is_supported(raw_lang):
                if normalized not in supported_langs:
                    supported_langs.append(normalized)
            else:
                if normalized not in unsupported_langs:
                    unsupported_langs.append(normalized)

        return all_langs, supported_langs, unsupported_langs

    def _group_files_by_language(
        self, repo_path: Path
    ) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Traverse directory tree and group relative file paths by normalized language.

        Args:
            repo_path: Base directory path to scan.

        Returns:
            Tuple of (file_groups_dict, language_file_counts_dict).
        """
        file_groups: Dict[str, List[str]] = {}
        counts: Dict[str, int] = {}

        if not repo_path.exists() or not repo_path.is_dir():
            return file_groups, counts

        for entry in repo_path.rglob("*"):
            if entry.is_file():
                lang = get_language_for_extension(entry.name)
                if lang:
                    rel_path = str(entry.relative_to(repo_path))
                    file_groups.setdefault(lang, []).append(rel_path)
                    counts[lang] = counts.get(lang, 0) + 1

        return file_groups, counts
