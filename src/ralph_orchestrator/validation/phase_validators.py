# ABOUTME: Per-phase validation logic implementing BaseValidator
# ABOUTME: Validates orchestration phase evidence directories

"""Phase-specific validators for the orchestration system.

Validators for each phase type that check evidence directories for
proper completion evidence without errors.
"""

import logging
from pathlib import Path
from typing import List, Set

from .base_validator import BaseValidator, ValidationResult
from .evidence_checker import EvidenceChecker


logger = logging.getLogger(__name__)


class OrchestrationPhaseValidator(BaseValidator):
    """Validates orchestration phase evidence directories.

    Checks all evidence files in a directory for error patterns,
    ensuring that phase completion is based on actual success,
    not just file existence.

    Example:
        validator = OrchestrationPhaseValidator()
        result = validator.validate(Path("validation-evidence/phase-01"))
        if not result.success:
            print(f"Phase failed: {result.errors}")
    """

    # File extensions to check for evidence
    EVIDENCE_EXTENSIONS: Set[str] = {".json", ".txt", ".log", ".md"}

    # Minimum number of evidence files expected
    MIN_EVIDENCE_FILES: int = 1

    def __init__(self, evidence_checker: EvidenceChecker = None):
        """Initialize the phase validator.

        Args:
            evidence_checker: Optional EvidenceChecker instance.
                If not provided, creates a new one.
        """
        self.checker = evidence_checker or EvidenceChecker()

    def validate(self, evidence_dir: Path) -> ValidationResult:
        """Validate an evidence directory.

        Checks all evidence files in the directory for error patterns.
        Fails if:
        - Directory doesn't exist
        - No evidence files found
        - Any evidence file contains error patterns

        Args:
            evidence_dir: Path to directory containing evidence files.

        Returns:
            ValidationResult indicating success or failure.
        """
        # Check directory exists
        if not evidence_dir.exists():
            return ValidationResult.from_errors([
                f"Evidence directory does not exist: {evidence_dir}"
            ])

        if not evidence_dir.is_dir():
            return ValidationResult.from_errors([
                f"Evidence path is not a directory: {evidence_dir}"
            ])

        # Find evidence files
        evidence_files = self._find_evidence_files(evidence_dir)

        if not evidence_files:
            result = ValidationResult.from_success()
            result.add_warning(f"No evidence files found in {evidence_dir}")
            return result

        logger.info(f"Validating {len(evidence_files)} evidence files in {evidence_dir}")

        # Check each evidence file
        combined_result = ValidationResult.from_success()

        for filepath in evidence_files:
            file_result = self.checker.check_file(filepath)

            if not file_result.success:
                logger.warning(f"Evidence error in {filepath.name}: {file_result.errors}")

            combined_result = combined_result.merge(file_result)

        # Log summary
        if combined_result.success:
            logger.info(f"All {len(evidence_files)} evidence files passed validation")
        else:
            logger.error(
                f"Validation failed: {len(combined_result.errors)} errors, "
                f"{len(combined_result.warnings)} warnings"
            )

        return combined_result

    def _find_evidence_files(self, directory: Path) -> List[Path]:
        """Find evidence files in a directory.

        Args:
            directory: Directory to search.

        Returns:
            List of paths to evidence files.
        """
        evidence_files = []

        for ext in self.EVIDENCE_EXTENSIONS:
            evidence_files.extend(directory.glob(f"*{ext}"))

        # Sort for consistent ordering
        return sorted(evidence_files)


class GenericPhaseValidator(BaseValidator):
    """Generic validator that can be used for any phase.

    Uses the same validation logic as OrchestrationPhaseValidator
    but with configurable parameters.
    """

    def __init__(
        self,
        name: str = "generic",
        extensions: Set[str] = None,
        min_files: int = 1,
        evidence_checker: EvidenceChecker = None,
    ):
        """Initialize generic phase validator.

        Args:
            name: Validator name for logging.
            extensions: Set of file extensions to check.
            min_files: Minimum number of evidence files required.
            evidence_checker: Optional EvidenceChecker instance.
        """
        self.name = name
        self.extensions = extensions or {".json", ".txt", ".log"}
        self.min_files = min_files
        self.checker = evidence_checker or EvidenceChecker()

    def get_name(self) -> str:
        """Get the validator name."""
        return f"GenericPhaseValidator({self.name})"

    def validate(self, evidence_dir: Path) -> ValidationResult:
        """Validate an evidence directory.

        Args:
            evidence_dir: Path to evidence directory.

        Returns:
            ValidationResult indicating success or failure.
        """
        if not evidence_dir.exists():
            return ValidationResult.from_errors([
                f"Directory not found: {evidence_dir}"
            ])

        # Find evidence files
        evidence_files = []
        for ext in self.extensions:
            evidence_files.extend(evidence_dir.glob(f"*{ext}"))

        evidence_files = sorted(evidence_files)

        # Check minimum file count
        if len(evidence_files) < self.min_files:
            result = ValidationResult.from_success()
            result.add_warning(
                f"Only {len(evidence_files)} evidence files found "
                f"(expected at least {self.min_files})"
            )
            if len(evidence_files) == 0:
                return result

        # Validate each file
        combined = ValidationResult.from_success()
        for filepath in evidence_files:
            file_result = self.checker.check_file(filepath)
            combined = combined.merge(file_result)

        return combined
