# ABOUTME: Tests for the validation system (Phase B3 - Rebuild Validation)
# ABOUTME: Tests EvidenceChecker, ValidationResult, PhaseValidator, ApprovalGate

"""Tests for the ralph_orchestrator.validation module.

The validation system provides semantic content validation for evidence files,
ensuring that success/failure is determined by actual content, not just file existence.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


class TestEvidenceChecker:
    """Tests for EvidenceChecker - semantic content validation."""

    def test_detect_not_found_error(self, tmp_path):
        """EvidenceChecker should detect 'not found' errors in JSON."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        # Create evidence file with "not found" error
        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{"detail": "Orchestrator not found"}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_detect_error_field(self, tmp_path):
        """EvidenceChecker should detect 'error' field in JSON."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{"error": "Internal server error"}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("error" in e.lower() for e in result.errors)

    def test_detect_status_error(self, tmp_path):
        """EvidenceChecker should detect status: error in JSON."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{"status": "error", "message": "Something failed"}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("status" in e.lower() or "error" in e.lower() for e in result.errors)

    def test_detect_status_fail(self, tmp_path):
        """EvidenceChecker should detect status: fail in JSON."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{"status": "fail", "data": null}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("fail" in e.lower() for e in result.errors)

    def test_detect_empty_response(self, tmp_path):
        """EvidenceChecker should detect empty JSON responses."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("empty" in e.lower() for e in result.errors)

    def test_detect_null_response(self, tmp_path):
        """EvidenceChecker should detect null JSON responses."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('null')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("null" in e.lower() or "empty" in e.lower() for e in result.errors)

    def test_pass_valid_json(self, tmp_path):
        """EvidenceChecker should pass valid JSON with no errors."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text(json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "hello",
            "session_id": "abc123"
        }))

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert result.success
        assert len(result.errors) == 0

    def test_detect_is_error_true(self, tmp_path):
        """EvidenceChecker should detect is_error: true in JSON."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{"is_error": true, "message": "Failed"}')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        assert not result.success
        assert any("is_error" in e.lower() or "error" in e.lower() for e in result.errors)

    def test_handle_invalid_json(self, tmp_path):
        """EvidenceChecker should handle invalid JSON gracefully."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "api-response.json"
        evidence_file.write_text('{ invalid json }')

        checker = EvidenceChecker()
        result = checker.check_json_for_errors(evidence_file)

        # Invalid JSON should be flagged as error
        assert not result.success
        assert any("json" in e.lower() or "parse" in e.lower() for e in result.errors)

    def test_check_evidence_freshness_stale(self, tmp_path):
        """EvidenceChecker should detect stale evidence files."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "old-evidence.txt"
        evidence_file.write_text("Test evidence")

        # Set file mtime to 48 hours ago
        old_time = time.time() - (48 * 3600)
        os.utime(evidence_file, (old_time, old_time))

        checker = EvidenceChecker()
        is_fresh = checker.check_evidence_freshness(evidence_file, max_age_hours=24)

        assert not is_fresh

    def test_check_evidence_freshness_fresh(self, tmp_path):
        """EvidenceChecker should pass fresh evidence files."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        evidence_file = tmp_path / "new-evidence.txt"
        evidence_file.write_text("Test evidence")

        checker = EvidenceChecker()
        is_fresh = checker.check_evidence_freshness(evidence_file, max_age_hours=24)

        assert is_fresh

    def test_check_text_file_for_errors(self, tmp_path):
        """EvidenceChecker should detect errors in plain text evidence."""
        from ralph_orchestrator.validation.evidence_checker import EvidenceChecker

        # Test with JSON content in a .txt file (common pattern)
        evidence_file = tmp_path / "control-api.txt"
        evidence_file.write_text('Response: {"detail":"Orchestrator not found"}')

        checker = EvidenceChecker()
        result = checker.check_text_for_errors(evidence_file)

        assert not result.success
        assert any("not found" in e.lower() for e in result.errors)


class TestValidationResult:
    """Tests for ValidationResult data class."""

    def test_success_result(self):
        """ValidationResult with no errors should be success."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result = ValidationResult(success=True, errors=[], warnings=[])

        assert result.success
        assert len(result.errors) == 0

    def test_failure_result(self):
        """ValidationResult with errors should be failure."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result = ValidationResult(
            success=False,
            errors=["File not found", "Invalid format"],
            warnings=[]
        )

        assert not result.success
        assert len(result.errors) == 2

    def test_from_errors_factory(self):
        """ValidationResult.from_errors should create failure result."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result = ValidationResult.from_errors(["Error 1", "Error 2"])

        assert not result.success
        assert len(result.errors) == 2

    def test_from_success_factory(self):
        """ValidationResult.from_success should create success result."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result = ValidationResult.from_success()

        assert result.success
        assert len(result.errors) == 0

    def test_add_warning(self):
        """ValidationResult should support adding warnings."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result = ValidationResult(success=True, errors=[], warnings=["Minor issue"])

        assert result.success  # Warnings don't affect success
        assert len(result.warnings) == 1

    def test_merge_results(self):
        """ValidationResult should support merging multiple results."""
        from ralph_orchestrator.validation.base_validator import ValidationResult

        result1 = ValidationResult.from_success()
        result1.warnings = ["Warning 1"]

        result2 = ValidationResult.from_errors(["Error 1"])

        merged = result1.merge(result2)

        assert not merged.success
        assert len(merged.errors) == 1
        assert len(merged.warnings) == 1


class TestBaseValidator:
    """Tests for BaseValidator abstract class."""

    def test_abstract_validate_method(self):
        """BaseValidator.validate should be abstract."""
        from ralph_orchestrator.validation.base_validator import BaseValidator

        # Should not be instantiable directly
        with pytest.raises(TypeError):
            BaseValidator()


class TestPhaseValidator:
    """Tests for PhaseValidator - per-phase validation logic."""

    def test_validate_good_evidence_directory(self, tmp_path):
        """PhaseValidator should pass directory with valid evidence."""
        from ralph_orchestrator.validation.phase_validators import OrchestrationPhaseValidator

        # Create evidence directory with good files
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Create valid JSON evidence
        (evidence_dir / "api-response.json").write_text(json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "test passed"
        }))

        # Create valid text evidence
        (evidence_dir / "output.txt").write_text("Test completed successfully")

        validator = OrchestrationPhaseValidator()
        result = validator.validate(evidence_dir)

        assert result.success

    def test_validate_bad_evidence_directory(self, tmp_path):
        """PhaseValidator should fail directory with error evidence."""
        from ralph_orchestrator.validation.phase_validators import OrchestrationPhaseValidator

        # Create evidence directory with error files
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Create JSON with error
        (evidence_dir / "api-response.json").write_text(json.dumps({
            "detail": "Orchestrator not found"
        }))

        validator = OrchestrationPhaseValidator()
        result = validator.validate(evidence_dir)

        assert not result.success
        assert len(result.errors) > 0

    def test_validate_empty_directory(self, tmp_path):
        """PhaseValidator should warn on empty evidence directory."""
        from ralph_orchestrator.validation.phase_validators import OrchestrationPhaseValidator

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        validator = OrchestrationPhaseValidator()
        result = validator.validate(evidence_dir)

        # Empty directory is a warning, not an error
        assert len(result.warnings) > 0 or not result.success

    def test_validate_nonexistent_directory(self, tmp_path):
        """PhaseValidator should fail on nonexistent directory."""
        from ralph_orchestrator.validation.phase_validators import OrchestrationPhaseValidator

        evidence_dir = tmp_path / "nonexistent"

        validator = OrchestrationPhaseValidator()
        result = validator.validate(evidence_dir)

        assert not result.success
        assert any("not exist" in e.lower() or "not found" in e.lower() for e in result.errors)

    def test_validate_mixed_evidence(self, tmp_path):
        """PhaseValidator should fail if any evidence shows errors."""
        from ralph_orchestrator.validation.phase_validators import OrchestrationPhaseValidator

        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()

        # Create one good file
        (evidence_dir / "good.json").write_text(json.dumps({
            "type": "success",
            "result": "ok"
        }))

        # Create one bad file
        (evidence_dir / "bad.json").write_text(json.dumps({
            "error": "Something went wrong"
        }))

        validator = OrchestrationPhaseValidator()
        result = validator.validate(evidence_dir)

        assert not result.success


class TestApprovalGate:
    """Tests for ApprovalGate - human confirmation."""

    def test_requires_approval_by_default(self):
        """ApprovalGate should require approval by default."""
        from ralph_orchestrator.validation.approval_gate import ApprovalGate

        gate = ApprovalGate()

        assert not gate.is_approved
        assert gate.requires_approval

    def test_approve_sets_approved(self):
        """ApprovalGate.approve should set is_approved to True."""
        from ralph_orchestrator.validation.approval_gate import ApprovalGate

        gate = ApprovalGate()
        gate.approve()

        assert gate.is_approved

    def test_reject_sets_rejected(self):
        """ApprovalGate.reject should keep is_approved False."""
        from ralph_orchestrator.validation.approval_gate import ApprovalGate

        gate = ApprovalGate()
        gate.reject(reason="Not ready")

        assert not gate.is_approved
        assert gate.rejection_reason == "Not ready"

    def test_auto_approve_mode(self):
        """ApprovalGate with auto_approve should start approved."""
        from ralph_orchestrator.validation.approval_gate import ApprovalGate

        gate = ApprovalGate(auto_approve=True)

        assert gate.is_approved
        assert not gate.requires_approval

    def test_request_approval_returns_message(self):
        """ApprovalGate.request_approval should return formatted message."""
        from ralph_orchestrator.validation.approval_gate import ApprovalGate
        from ralph_orchestrator.validation.base_validator import ValidationResult

        gate = ApprovalGate()
        result = ValidationResult.from_success()
        result.warnings = ["Minor issue detected"]

        message = gate.request_approval(result)

        assert isinstance(message, str)
        assert len(message) > 0


class TestValidationIntegration:
    """Integration tests for the validation system."""

    def test_end_to_end_validation_pass(self, tmp_path):
        """Full validation pipeline should pass with good evidence."""
        from ralph_orchestrator.validation import validate_evidence_directory

        # Create evidence directory with valid files
        evidence_dir = tmp_path / "validation-evidence" / "test-phase"
        evidence_dir.mkdir(parents=True)

        (evidence_dir / "api-test.json").write_text(json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "All tests passed"
        }))

        (evidence_dir / "output.txt").write_text("Validation complete: PASS")

        result = validate_evidence_directory(evidence_dir)

        assert result.success

    def test_end_to_end_validation_fail(self, tmp_path):
        """Full validation pipeline should fail with error evidence."""
        from ralph_orchestrator.validation import validate_evidence_directory

        evidence_dir = tmp_path / "validation-evidence" / "test-phase"
        evidence_dir.mkdir(parents=True)

        # Known bad evidence pattern
        (evidence_dir / "control-api.txt").write_text(
            'API Response: {"detail":"Orchestrator not found"}'
        )

        result = validate_evidence_directory(evidence_dir)

        assert not result.success
        assert any("not found" in e.lower() for e in result.errors)
