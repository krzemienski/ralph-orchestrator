# ABOUTME: Integration tests package for Ralph Orchestrator
# ABOUTME: Tests that use real Claude CLI and validate end-to-end flows

"""Integration tests for Ralph Orchestrator.

These tests spawn real Claude CLI processes and validate actual orchestration flows.
They are marked with @pytest.mark.integration and @pytest.mark.slow.

Run with: pytest -m integration
Skip with: pytest -m "not integration"
"""
