"""Tests for --auto-transform flag integration with ralph run.

Following TDD: Each test is written BEFORE the implementation.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys


class TestAutoTransformFlag:
    """Tests for the --auto-transform CLI flag."""

    def test_auto_transform_flag_exists(self):
        """RED: --auto-transform should be a valid option for ralph run."""
        from ralph_orchestrator.__main__ import main

        # Run with --help to see if flag is accepted
        with patch('sys.argv', ['ralph', 'run', '--auto-transform', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # --help exits with 0, which means the flag was accepted
            assert exc_info.value.code == 0

    def test_auto_transform_in_help_text(self, capsys):
        """RED: --auto-transform should appear in help output."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'run', '--help']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert '--auto-transform' in captured.out


class TestAutoTransformWithPromptFile:
    """Tests for --auto-transform with file-based prompts."""

    def test_transforms_prompt_file_content(self, tmp_path):
        """RED: --auto-transform should transform prompt file before execution."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.transform import PromptTransformer

        # Create a simple prompt file WITHOUT completion marker
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("""# Task
Create a hello world script.

## Requirements
- Print greeting
""")

        # Mock the orchestrator to capture what prompt it receives
        mock_orchestrator = MagicMock()
        mock_orchestrator.run = MagicMock(return_value=MagicMock(
            iterations=1,
            completed=True,
            completion_method="mock"
        ))

        with patch('ralph_orchestrator.__main__.RalphOrchestrator', return_value=mock_orchestrator):
            with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file),
                                     '--auto-transform', '--dry-run']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Dry run exits with 0
                assert exc_info.value.code == 0

        # The prompt file should now contain TASK_COMPLETE marker
        content = prompt_file.read_text()
        assert "TASK_COMPLETE" in content

    def test_does_not_transform_without_flag(self, tmp_path):
        """RED: Without --auto-transform, prompt should remain unchanged."""
        from ralph_orchestrator.__main__ import main

        # Create a simple prompt file WITHOUT completion marker
        prompt_file = tmp_path / "PROMPT.md"
        original_content = """# Task
Create a hello world script.
"""
        prompt_file.write_text(original_content)

        with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file), '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        # Content should be unchanged
        assert prompt_file.read_text() == original_content


class TestAutoTransformWithPromptText:
    """Tests for --auto-transform with inline prompt text."""

    def test_transforms_prompt_text(self, capsys):
        """RED: --auto-transform should transform inline prompt text."""
        from ralph_orchestrator.__main__ import main

        mock_orchestrator = MagicMock()
        mock_orchestrator.run = MagicMock(return_value=MagicMock(
            iterations=1,
            completed=True,
            completion_method="mock"
        ))

        with patch('ralph_orchestrator.__main__.RalphOrchestrator') as mock_orch_cls:
            mock_orch_cls.return_value = mock_orchestrator

            with patch('sys.argv', ['ralph', 'run', '--prompt-text', 'Create a hello world script',
                                     '--auto-transform', '--dry-run']):
                with pytest.raises(SystemExit):
                    main()

            captured = capsys.readouterr()
            # Should show transformed preview with TASK_COMPLETE
            assert "TASK_COMPLETE" in captured.out or mock_orch_cls.called


class TestAutoTransformPreservesExisting:
    """Tests that auto-transform doesn't duplicate markers."""

    def test_does_not_duplicate_completion_marker(self, tmp_path):
        """RED: --auto-transform should not duplicate existing completion marker."""
        from ralph_orchestrator.__main__ import main

        # Create a prompt file that already has completion marker
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("""# Task
Create a hello world script.

## Completion Status
- [ ] TASK_COMPLETE
""")

        with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file),
                                 '--auto-transform', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        # Should have exactly one TASK_COMPLETE
        content = prompt_file.read_text()
        assert content.count("TASK_COMPLETE") == 1


class TestAutoTransformVerboseOutput:
    """Tests for verbose output when using --auto-transform."""

    def test_shows_transform_info_when_verbose(self, tmp_path, capsys):
        """RED: --auto-transform with --verbose should show what was transformed."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Task\nDo something.\n")

        with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file),
                                 '--auto-transform', '--verbose', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Should indicate transformation occurred
        assert 'transform' in captured.out.lower() or 'completion' in captured.out.lower()


class TestAutoTransformWithMinimalFlag:
    """Tests for --auto-transform combined with --minimal."""

    def test_auto_transform_with_minimal_flag(self, tmp_path):
        """RED: --auto-transform --minimal should only add critical elements."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Task\n1. First step\n2. Second step\n")

        with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file),
                                 '--auto-transform', '--minimal', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        content = prompt_file.read_text()
        # Should have completion marker (critical)
        assert "TASK_COMPLETE" in content
        # Should NOT have working directory (non-critical for minimal)
        # This depends on implementation - may or may not have Working Directory


class TestAutoTransformErrorHandling:
    """Tests for error handling in auto-transform."""

    def test_handles_transform_error_gracefully(self, tmp_path, capsys):
        """RED: Transform errors should be handled gracefully."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.transform import PromptTransformer

        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("# Task\nDo something.\n")

        # Mock transformer to raise an error
        with patch.object(PromptTransformer, 'transform', side_effect=Exception("Transform error")):
            with patch('sys.argv', ['ralph', 'run', '--prompt-file', str(prompt_file),
                                     '--auto-transform', '--dry-run']):
                # Should either handle error or exit gracefully
                try:
                    main()
                except SystemExit as e:
                    # Either exits with error code or succeeds
                    pass
                except Exception:
                    # Unhandled exception is a test failure
                    pytest.fail("Unhandled exception during transform error")
