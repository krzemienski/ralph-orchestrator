"""Validators for transformed prompts.

Ensures the transformed prompt is well-formed and complete.
"""
from typing import List


class TransformValidator:
    """Validates transformed prompts."""

    def validate(self, prompt: str) -> dict:
        """Validate a transformed prompt.

        Args:
            prompt: The transformed prompt text

        Returns:
            Dictionary with:
            - valid: bool
            - errors: List of error messages
            - warnings: List of warning messages
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for completion marker
        if "TASK_COMPLETE" not in prompt and "LOOP_COMPLETE" not in prompt:
            warnings.append("No completion marker found")

        # Check for at least one requirement indicator
        has_requirements = any([
            "- [ ]" in prompt,
            "- [x]" in prompt,
            "## Requirements" in prompt.lower(),
        ])
        if not has_requirements:
            warnings.append("No clear requirements section found")

        # Check for empty prompt
        if not prompt.strip():
            errors.append("Prompt is empty")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


def validate_completion_marker(prompt: str) -> bool:
    """Quick check for completion marker presence."""
    return "TASK_COMPLETE" in prompt or "LOOP_COMPLETE" in prompt


def validate_working_directory(prompt: str) -> bool:
    """Quick check for working directory in context."""
    return "Working Directory:" in prompt
