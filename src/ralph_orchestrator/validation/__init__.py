# ABOUTME: Validation module public API for evidence validation
# ABOUTME: Phase B3 fix for broken validation that checked file existence, not content

"""Validation module for Ralph Orchestrator.

This module provides semantic content validation for evidence files,
fixing the broken validation system that only checked file existence.

Key Features:
    - EvidenceChecker: Detects error patterns in JSON/text files
    - ValidationResult: Structured result with errors and warnings
    - PhaseValidator: Per-phase validation logic
    - ApprovalGate: Human confirmation for TASK_COMPLETE

The Problem Fixed:
    The original validation in orchestrator.py marked errors as SUCCESS
    because it only checked file existence, not content. For example:
    - Evidence file: {"detail":"Orchestrator not found"}
    - Old validation: PASS (file exists)
    - New validation: FAIL (error detected in content)

Example Usage:
    from ralph_orchestrator.validation import validate_evidence_directory

    result = validate_evidence_directory(Path("validation-evidence/phase-01"))
    if not result.success:
        print(f"Validation failed: {result.errors}")

Public API:
    - validate_evidence_directory: Main entry point for validation
    - EvidenceChecker: Low-level content checking
    - ValidationResult: Result data class
    - BaseValidator: Abstract validator interface
    - OrchestrationPhaseValidator: Standard phase validator
    - ApprovalGate: Human confirmation gate
"""

from pathlib import Path
from typing import Optional

from .base_validator import BaseValidator, ValidationResult
from .evidence_checker import EvidenceChecker
from .phase_validators import OrchestrationPhaseValidator, GenericPhaseValidator
from .approval_gate import ApprovalGate, AutoApprovalGate


__all__ = [
    # Main entry point
    "validate_evidence_directory",
    # Core classes
    "EvidenceChecker",
    "ValidationResult",
    # Validators
    "BaseValidator",
    "OrchestrationPhaseValidator",
    "GenericPhaseValidator",
    # Approval
    "ApprovalGate",
    "AutoApprovalGate",
]


def validate_evidence_directory(
    evidence_dir: Path,
    validator: Optional[BaseValidator] = None,
) -> ValidationResult:
    """Validate an evidence directory for errors.

    Main entry point for the validation module. Checks all evidence files
    in the given directory for error patterns.

    Args:
        evidence_dir: Path to directory containing evidence files.
        validator: Optional custom validator. If not provided, uses
            OrchestrationPhaseValidator.

    Returns:
        ValidationResult with success=True if all evidence is valid,
        or success=False with error details if any issues detected.

    Example:
        # Basic usage
        result = validate_evidence_directory(Path("validation-evidence/phase-01"))

        # With custom validator
        custom = GenericPhaseValidator(name="custom", min_files=3)
        result = validate_evidence_directory(path, validator=custom)
    """
    if validator is None:
        validator = OrchestrationPhaseValidator()

    return validator.validate(evidence_dir)
