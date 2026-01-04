# ABOUTME: Human confirmation gate for validation before TASK_COMPLETE
# ABOUTME: Blocks task completion until human approves validation results

"""Approval gate for human confirmation of validation results.

Provides a mechanism to require human approval before marking a task
as complete, ensuring that automated validation is reviewed.
"""

import logging
from datetime import datetime
from typing import Optional

from .base_validator import ValidationResult


logger = logging.getLogger(__name__)


class ApprovalGate:
    """Gate that requires human approval for task completion.

    The approval gate blocks TASK_COMPLETE status until a human
    reviews and approves the validation results.

    Example:
        gate = ApprovalGate()
        result = validator.validate(evidence_dir)

        if result.success:
            message = gate.request_approval(result)
            print(message)
            # User reviews and approves
            gate.approve()

        if gate.is_approved:
            mark_task_complete()
    """

    def __init__(self, auto_approve: bool = False):
        """Initialize the approval gate.

        Args:
            auto_approve: If True, gate starts approved (for CI/CD).
        """
        self._is_approved = auto_approve
        self._requires_approval = not auto_approve
        self._rejection_reason: Optional[str] = None
        self._approved_at: Optional[datetime] = None
        self._rejected_at: Optional[datetime] = None
        self._approval_message: Optional[str] = None

    @property
    def is_approved(self) -> bool:
        """Check if gate has been approved."""
        return self._is_approved

    @property
    def requires_approval(self) -> bool:
        """Check if gate requires approval."""
        return self._requires_approval

    @property
    def rejection_reason(self) -> Optional[str]:
        """Get the reason for rejection, if any."""
        return self._rejection_reason

    @property
    def approved_at(self) -> Optional[datetime]:
        """Get the timestamp when approved."""
        return self._approved_at

    def approve(self, message: Optional[str] = None) -> None:
        """Approve the gate, allowing task completion.

        Args:
            message: Optional approval message/notes.
        """
        self._is_approved = True
        self._approved_at = datetime.now()
        self._approval_message = message
        self._rejection_reason = None
        self._rejected_at = None

        logger.info(f"Approval gate passed at {self._approved_at}")
        if message:
            logger.info(f"Approval message: {message}")

    def reject(self, reason: str) -> None:
        """Reject the gate, blocking task completion.

        Args:
            reason: Explanation for why approval was rejected.
        """
        self._is_approved = False
        self._rejection_reason = reason
        self._rejected_at = datetime.now()
        self._approved_at = None
        self._approval_message = None

        logger.warning(f"Approval gate rejected: {reason}")

    def reset(self) -> None:
        """Reset the gate to unapproved state."""
        self._is_approved = False
        self._rejection_reason = None
        self._approved_at = None
        self._rejected_at = None
        self._approval_message = None

    def request_approval(self, validation_result: ValidationResult) -> str:
        """Generate an approval request message.

        Creates a formatted message presenting the validation results
        for human review.

        Args:
            validation_result: The validation result to present.

        Returns:
            Formatted approval request message.
        """
        lines = [
            "=" * 60,
            "VALIDATION APPROVAL REQUIRED",
            "=" * 60,
            "",
        ]

        # Status summary
        status = "PASSED" if validation_result.success else "FAILED"
        lines.append(f"Validation Status: {status}")
        lines.append("")

        # Errors (if any)
        if validation_result.errors:
            lines.append(f"Errors ({len(validation_result.errors)}):")
            for error in validation_result.errors:
                lines.append(f"  [ERROR] {error}")
            lines.append("")

        # Warnings (if any)
        if validation_result.warnings:
            lines.append(f"Warnings ({len(validation_result.warnings)}):")
            for warning in validation_result.warnings:
                lines.append(f"  [WARN] {warning}")
            lines.append("")

        # Action prompt
        if validation_result.success:
            lines.extend([
                "All validations passed. Approve to mark task complete?",
                "",
                "Actions:",
                "  [A]pprove - Mark task as complete",
                "  [R]eject  - Request additional work",
            ])
        else:
            lines.extend([
                "Validation failed. Review errors above.",
                "",
                "Actions:",
                "  [R]eject  - Block task completion (recommended)",
                "  [O]verride - Force approve despite errors (not recommended)",
            ])

        lines.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(lines)

    def get_status_summary(self) -> str:
        """Get a brief status summary.

        Returns:
            One-line status description.
        """
        if self._is_approved:
            return f"Approved at {self._approved_at}"
        elif self._rejection_reason:
            return f"Rejected: {self._rejection_reason}"
        else:
            return "Pending approval"


class AutoApprovalGate(ApprovalGate):
    """Approval gate that auto-approves based on validation result.

    For CI/CD pipelines where human interaction is not possible,
    this gate automatically approves if validation passes.
    """

    def __init__(self):
        """Initialize auto-approval gate."""
        super().__init__(auto_approve=False)

    def check_and_approve(self, validation_result: ValidationResult) -> bool:
        """Check validation result and auto-approve if passed.

        Args:
            validation_result: The validation result to check.

        Returns:
            True if approved, False if rejected.
        """
        if validation_result.success:
            self.approve("Auto-approved: validation passed")
            return True
        else:
            self.reject(
                f"Auto-rejected: {len(validation_result.errors)} errors detected"
            )
            return False
