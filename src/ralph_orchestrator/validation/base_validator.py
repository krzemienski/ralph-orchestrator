# ABOUTME: Abstract base class for validators and ValidationResult data class
# ABOUTME: Provides interface for phase-specific validation implementations

"""Base validator interface and ValidationResult for the validation system.

The validation system provides semantic content validation for evidence files,
going beyond file existence checks to analyze actual content for errors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        success: True if validation passed, False if any errors.
        errors: List of error messages that caused validation failure.
        warnings: List of warning messages (don't affect success).
    """
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_errors(cls, errors: List[str]) -> "ValidationResult":
        """Create a failure result from a list of errors.

        Args:
            errors: List of error messages.

        Returns:
            ValidationResult with success=False and the given errors.
        """
        return cls(success=False, errors=list(errors), warnings=[])

    @classmethod
    def from_success(cls, warnings: Optional[List[str]] = None) -> "ValidationResult":
        """Create a success result with optional warnings.

        Args:
            warnings: Optional list of warning messages.

        Returns:
            ValidationResult with success=True and optional warnings.
        """
        return cls(success=True, errors=[], warnings=list(warnings or []))

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge this result with another, combining errors and warnings.

        The merged result fails if either input result failed.

        Args:
            other: Another ValidationResult to merge with.

        Returns:
            New ValidationResult with combined errors and warnings.
        """
        return ValidationResult(
            success=self.success and other.success,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )

    def add_error(self, error: str) -> None:
        """Add an error message and mark as failed.

        Args:
            error: Error message to add.
        """
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message (does not affect success).

        Args:
            warning: Warning message to add.
        """
        self.warnings.append(warning)

    def __str__(self) -> str:
        """Human-readable representation of the result."""
        status = "PASS" if self.success else "FAIL"
        parts = [f"Validation {status}"]

        if self.errors:
            parts.append(f"Errors ({len(self.errors)}):")
            for e in self.errors:
                parts.append(f"  - {e}")

        if self.warnings:
            parts.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                parts.append(f"  - {w}")

        return "\n".join(parts)


class BaseValidator(ABC):
    """Abstract base class for validators.

    Validators check evidence directories/files for specific phases
    and return ValidationResult indicating success or failure.

    Subclasses must implement the validate() method.
    """

    @abstractmethod
    def validate(self, evidence_dir: Path) -> ValidationResult:
        """Validate an evidence directory.

        Args:
            evidence_dir: Path to directory containing evidence files.

        Returns:
            ValidationResult indicating success or failure with details.
        """
        pass

    def get_name(self) -> str:
        """Get the validator name for logging.

        Returns:
            Human-readable name of this validator.
        """
        return self.__class__.__name__
