# ABOUTME: Test suite for the validation feature
# ABOUTME: Tests validation parameters, proposal flow, and Claude-only guard

"""Tests for Ralph Orchestrator Validation Feature."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from ralph_orchestrator.orchestrator import RalphOrchestrator


class TestValidationParameters(unittest.TestCase):
    """Test validation feature parameters on RalphOrchestrator."""

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_enable_validation_parameter_defaults_to_false(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test enable_validation parameter defaults to False (opt-in)."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
            )

            # enable_validation should default to False
            self.assertFalse(orchestrator.enable_validation)
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_enable_validation_parameter_can_be_set_true(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test enable_validation parameter can be set to True."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
                enable_validation=True,
            )

            self.assertTrue(orchestrator.enable_validation)
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_interactive_parameter_defaults_to_true(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test validation_interactive parameter defaults to True."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
            )

            # validation_interactive should default to True
            self.assertTrue(orchestrator.validation_interactive)
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_proposal_attribute_exists(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test validation_proposal attribute exists and is None by default."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
            )

            # validation_proposal should exist and be None
            self.assertIsNone(orchestrator.validation_proposal)
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_approved_attribute_exists(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test validation_approved attribute exists and is False by default."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
            )

            # validation_approved should exist and be False
            self.assertFalse(orchestrator.validation_approved)
        finally:
            Path(prompt_file).unlink()


class TestValidationClaudeOnlyGuard(unittest.TestCase):
    """Test validation feature only works with Claude adapter."""

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_with_non_claude_raises_valueerror(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test ValueError raised when enable_validation=True with non-Claude adapter."""
        # Setup qchat as available
        mock_qchat_instance = MagicMock()
        mock_qchat_instance.available = True
        mock_qchat.return_value = mock_qchat_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            with self.assertRaises(ValueError) as context:
                RalphOrchestrator(
                    prompt_file_or_config=prompt_file,
                    primary_tool="qchat",
                    enable_validation=True,
                )

            self.assertIn("Claude", str(context.exception))
            self.assertIn("qchat", str(context.exception))
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_with_gemini_raises_valueerror(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test ValueError raised when enable_validation=True with Gemini adapter."""
        mock_gemini_instance = MagicMock()
        mock_gemini_instance.available = True
        mock_gemini.return_value = mock_gemini_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            with self.assertRaises(ValueError) as context:
                RalphOrchestrator(
                    prompt_file_or_config=prompt_file,
                    primary_tool="gemini",
                    enable_validation=True,
                )

            self.assertIn("Claude", str(context.exception))
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_validation_with_claude_succeeds(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test validation with Claude adapter succeeds."""
        mock_claude_instance = MagicMock()
        mock_claude_instance.available = True
        mock_claude.return_value = mock_claude_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            # Should not raise
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="claude",
                enable_validation=True,
            )

            self.assertTrue(orchestrator.enable_validation)
        finally:
            Path(prompt_file).unlink()

    @patch('ralph_orchestrator.orchestrator.ClaudeAdapter')
    @patch('ralph_orchestrator.orchestrator.QChatAdapter')
    @patch('ralph_orchestrator.orchestrator.GeminiAdapter')
    @patch('ralph_orchestrator.orchestrator.ACPAdapter')
    def test_no_error_when_validation_disabled_with_non_claude(
        self, mock_acp, mock_gemini, mock_qchat, mock_claude
    ):
        """Test no error when enable_validation=False with non-Claude adapter."""
        mock_qchat_instance = MagicMock()
        mock_qchat_instance.available = True
        mock_qchat.return_value = mock_qchat_instance

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Task")
            prompt_file = f.name

        try:
            # Should not raise when validation is disabled (default)
            orchestrator = RalphOrchestrator(
                prompt_file_or_config=prompt_file,
                primary_tool="qchat",
                enable_validation=False,  # Explicitly disabled
            )

            self.assertFalse(orchestrator.enable_validation)
        finally:
            Path(prompt_file).unlink()


if __name__ == "__main__":
    unittest.main()
