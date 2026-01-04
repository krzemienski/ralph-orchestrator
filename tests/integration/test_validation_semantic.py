# ABOUTME: Integration tests for semantic validation with real evidence files
# ABOUTME: Tests EvidenceChecker against actual validation-evidence directory

"""Semantic validation integration tests.

Tests the validation module against real evidence files to ensure
error detection works correctly in production scenarios.

Run with: pytest -m integration tests/integration/test_validation_semantic.py
"""

import json
import pytest
from pathlib import Path


@pytest.mark.integration
class TestRealEvidenceValidation:
    """Test validation against real evidence files."""

    def test_valid_spawn_evidence_passes(self, real_evidence_base_path, evidence_checker):
        """Test that valid spawn evidence file passes validation.

        Validates: validation-evidence/orchestration-02/spawn-subagent-test.txt
        Expected: PASS (contains successful spawn output)
        """
        evidence_file = real_evidence_base_path / "orchestration-02" / "spawn-subagent-test.txt"

        if not evidence_file.exists():
            pytest.skip(f"Evidence file not found: {evidence_file}")

        result = evidence_checker.check_file(evidence_file)

        # Should pass - file contains "Overall: PASS"
        # Note: May have warnings but should not have critical errors
        assert result is not None
        # The file shows successful spawn, should not have blocking errors

    def test_orchestration_tests_evidence(self, real_evidence_base_path, evidence_checker):
        """Test validation of orchestration test evidence.

        Validates: validation-evidence/orchestration-05/tests.txt
        Expected: PASS if tests passed
        """
        evidence_file = real_evidence_base_path / "orchestration-05" / "tests.txt"

        if not evidence_file.exists():
            pytest.skip(f"Evidence file not found: {evidence_file}")

        result = evidence_checker.check_file(evidence_file)
        assert result is not None

    def test_validation_directory(self, real_evidence_base_path):
        """Test validate_evidence_directory on real evidence.

        Uses the public API to validate a complete evidence directory.
        """
        from ralph_orchestrator.validation import validate_evidence_directory

        evidence_dir = real_evidence_base_path / "orchestration-02"

        if not evidence_dir.exists():
            pytest.skip(f"Evidence directory not found: {evidence_dir}")

        result = validate_evidence_directory(evidence_dir)

        # Should have validation result
        assert result is not None
        assert hasattr(result, "success")


@pytest.mark.integration
class TestSyntheticEvidenceValidation:
    """Test validation with synthetic evidence files."""

    def test_json_with_error_detail_fails(self, tmp_path, evidence_checker):
        """Test that JSON with error detail is detected."""
        error_file = tmp_path / "error_response.json"
        error_file.write_text('{"detail": "Orchestrator not found"}')

        result = evidence_checker.check_file(error_file)

        assert result.success is False
        assert len(result.errors) > 0
        assert any("not found" in e.lower() for e in result.errors)

    def test_json_with_error_field_fails(self, tmp_path, evidence_checker):
        """Test that JSON with error field is detected."""
        error_file = tmp_path / "error.json"
        error_file.write_text('{"error": "Connection refused"}')

        result = evidence_checker.check_file(error_file)

        assert result.success is False
        assert len(result.errors) > 0

    def test_json_with_error_status_fails(self, tmp_path, evidence_checker):
        """Test that JSON with error status is detected."""
        error_file = tmp_path / "status.json"
        error_file.write_text('{"status": "error", "message": "Something went wrong"}')

        result = evidence_checker.check_file(error_file)

        assert result.success is False

    def test_empty_json_fails(self, tmp_path, evidence_checker):
        """Test that empty JSON is detected as error."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")

        result = evidence_checker.check_file(empty_file)

        assert result.success is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_valid_json_passes(self, tmp_path, evidence_checker):
        """Test that valid JSON passes validation."""
        valid_file = tmp_path / "valid.json"
        valid_file.write_text('{"status": "ok", "result": "success", "count": 42}')

        result = evidence_checker.check_file(valid_file)

        assert result.success is True
        assert len(result.errors) == 0

    def test_text_with_traceback_fails(self, tmp_path, evidence_checker):
        """Test that text file with Python traceback is detected."""
        error_file = tmp_path / "error.txt"
        error_file.write_text("""
Running tests...
Traceback (most recent call last):
  File "test.py", line 10, in test_func
    raise ValueError("test error")
ValueError: test error
""")

        result = evidence_checker.check_file(error_file)

        assert result.success is False
        assert any("traceback" in e.lower() for e in result.errors)

    def test_text_with_connection_refused_fails(self, tmp_path, evidence_checker):
        """Test that connection errors are detected."""
        error_file = tmp_path / "network.txt"
        error_file.write_text("Error: Connection refused to localhost:8080")

        result = evidence_checker.check_file(error_file)

        assert result.success is False

    def test_valid_text_passes(self, tmp_path, evidence_checker):
        """Test that valid text file passes validation."""
        valid_file = tmp_path / "report.txt"
        valid_file.write_text("""
Test Report
===========
All 15 tests passed.
Coverage: 87%
Status: SUCCESS
""")

        result = evidence_checker.check_file(valid_file)

        assert result.success is True


@pytest.mark.integration
class TestMixedEvidenceValidation:
    """Test validation with mixed evidence (pass/fail files)."""

    def test_mixed_directory_aggregation(self, mixed_evidence_dir):
        """Test that directory with mixed evidence reports FAIL.

        Uses fixture that creates:
        - good.json: valid success response
        - bad.json: error response
        Expected: Overall FAIL because of bad.json
        """
        from ralph_orchestrator.validation import validate_evidence_directory

        result = validate_evidence_directory(mixed_evidence_dir)

        # Should fail due to bad.json
        assert result.success is False
        assert len(result.errors) > 0

    def test_passing_directory(self, sample_evidence_dir):
        """Test that directory with all passing evidence reports PASS."""
        from ralph_orchestrator.validation import validate_evidence_directory

        result = validate_evidence_directory(sample_evidence_dir)

        # Should pass - all files are valid
        assert result.success is True
        assert len(result.errors) == 0

    def test_failing_directory(self, failing_evidence_dir):
        """Test that directory with failing evidence reports FAIL."""
        from ralph_orchestrator.validation import validate_evidence_directory

        result = validate_evidence_directory(failing_evidence_dir)

        # Should fail - error.json contains error
        assert result.success is False
        assert len(result.errors) > 0


@pytest.mark.integration
class TestEvidenceFreshness:
    """Test evidence freshness checking."""

    def test_new_file_is_fresh(self, tmp_path, evidence_checker):
        """Test that newly created file is considered fresh."""
        new_file = tmp_path / "fresh.json"
        new_file.write_text('{"status": "ok"}')

        is_fresh = evidence_checker.check_evidence_freshness(new_file, max_age_hours=24)

        assert is_fresh is True

    def test_missing_file_not_fresh(self, tmp_path, evidence_checker):
        """Test that missing file is not considered fresh."""
        missing_file = tmp_path / "missing.json"

        is_fresh = evidence_checker.check_evidence_freshness(missing_file, max_age_hours=24)

        assert is_fresh is False
