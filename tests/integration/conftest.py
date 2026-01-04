# ABOUTME: Pytest configuration and fixtures for integration tests
# ABOUTME: Provides fixtures for OrchestrationManager, EvidenceChecker, and temp directories

"""Pytest fixtures for integration tests.

Provides fixtures for:
- OrchestrationManager with temp directory
- EvidenceChecker instance
- Async utilities for Claude CLI spawning

Note: Markers (integration, slow) are defined in parent conftest.py
"""

import pytest
from pathlib import Path


@pytest.fixture
def orchestration_manager(tmp_path):
    """Create OrchestrationManager with temp directory.

    Returns:
        OrchestrationManager instance with base_dir set to tmp_path.
    """
    from ralph_orchestrator.main import RalphConfig
    from ralph_orchestrator.orchestration import OrchestrationManager

    config = RalphConfig(enable_orchestration=True)
    manager = OrchestrationManager(config, base_dir=tmp_path)
    return manager


@pytest.fixture
def initialized_orchestration_manager(tmp_path):
    """Create OrchestrationManager with coordination initialized.

    Returns:
        OrchestrationManager with coordinator.init_coordination() called.
    """
    from ralph_orchestrator.main import RalphConfig
    from ralph_orchestrator.orchestration import OrchestrationManager

    config = RalphConfig(enable_orchestration=True)
    manager = OrchestrationManager(config, base_dir=tmp_path)
    manager.coordinator.init_coordination()
    return manager


@pytest.fixture
def evidence_checker():
    """Create EvidenceChecker instance.

    Returns:
        EvidenceChecker ready to validate evidence files.
    """
    from ralph_orchestrator.validation import EvidenceChecker

    return EvidenceChecker()


@pytest.fixture
def sample_evidence_dir(tmp_path):
    """Create a temporary directory with sample evidence files.

    Returns:
        Path to temp directory with sample evidence files.
    """
    # Create a passing evidence file
    passing_file = tmp_path / "passing.json"
    passing_file.write_text('{"status": "success", "result": "test passed"}')

    # Create a passing text file
    passing_txt = tmp_path / "report.txt"
    passing_txt.write_text("Test completed successfully.\nAll assertions passed.")

    return tmp_path


@pytest.fixture
def failing_evidence_dir(tmp_path):
    """Create a temporary directory with failing evidence files.

    Returns:
        Path to temp directory with error-containing evidence files.
    """
    # Create a failing evidence file
    failing_file = tmp_path / "error.json"
    failing_file.write_text('{"detail": "Orchestrator not found"}')

    return tmp_path


@pytest.fixture
def mixed_evidence_dir(tmp_path):
    """Create a temporary directory with mixed (pass/fail) evidence.

    Returns:
        Path to temp directory with both passing and failing evidence.
    """
    # Create passing file
    passing_file = tmp_path / "good.json"
    passing_file.write_text('{"status": "ok", "result": "success"}')

    # Create failing file
    failing_file = tmp_path / "bad.json"
    failing_file.write_text('{"error": "Something went wrong"}')

    return tmp_path


@pytest.fixture
def real_evidence_base_path():
    """Return path to real validation-evidence directory.

    Returns:
        Path to validation-evidence/ directory in project root.
    """
    # Navigate from tests/integration to project root
    return Path(__file__).parent.parent.parent / "validation-evidence"
