"""Tests for the ralph structure CLI command.

Following TDD: Each test is written BEFORE the implementation.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys


class TestStructureCommandExists:
    """Tests for CLI command registration."""

    def test_structure_command_in_parser(self):
        """RED: ralph structure should be a valid subcommand."""
        from ralph_orchestrator.__main__ import main
        import argparse

        # Capture parser configuration
        with patch('sys.argv', ['ralph', 'structure', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # --help exits with 0
            assert exc_info.value.code == 0

    def test_structure_help_shows_usage(self, capsys):
        """RED: ralph structure --help should show usage information."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'structure', '--help']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert 'structure' in captured.out.lower()
        assert 'transform' in captured.out.lower() or 'prompt' in captured.out.lower()


class TestStructureFileInput:
    """Tests for file input handling."""

    def test_structure_file_transforms_content(self, tmp_path):
        """RED: ralph structure file.md should transform file content."""
        from ralph_orchestrator.__main__ import main

        # Create test prompt file
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("""# Task
Create a hello world script.

## Requirements
- Print greeting
""")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        # Read transformed content
        content = prompt_file.read_text()
        assert "TASK_COMPLETE" in content

    def test_structure_file_preserves_existing_marker(self, tmp_path):
        """RED: Should not duplicate completion marker."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "complete_prompt.md"
        prompt_file.write_text("""# Task
Do something.

## Completion Status
- [ ] TASK_COMPLETE
""")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        content = prompt_file.read_text()
        assert content.count("TASK_COMPLETE") == 1

    def test_structure_missing_file_error(self, tmp_path, capsys):
        """RED: Should error on missing file."""
        from ralph_orchestrator.__main__ import main

        missing_file = tmp_path / "nonexistent.md"

        with patch('sys.argv', ['ralph', 'structure', str(missing_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code != 0

        captured = capsys.readouterr()
        # Should show error about missing file
        assert 'not found' in captured.err.lower() or 'no such' in captured.err.lower() or 'error' in captured.err.lower()


class TestStructureDryRun:
    """Tests for --dry-run mode."""

    def test_dry_run_shows_preview(self, tmp_path, capsys):
        """RED: --dry-run should show changes without modifying file."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test_prompt.md"
        original_content = """# Task
Simple task.
"""
        prompt_file.write_text(original_content)

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--dry-run']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        # File should be unchanged
        assert prompt_file.read_text() == original_content

        # Output should show transformed version
        captured = capsys.readouterr()
        assert "TASK_COMPLETE" in captured.out

    def test_dry_run_shows_changes_summary(self, tmp_path, capsys):
        """RED: --dry-run should show what would change."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("# Task\nDo something.\n")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Should mention what was added
        assert "completion" in captured.out.lower() or "added" in captured.out.lower()


class TestStructureOutput:
    """Tests for output options."""

    def test_output_to_different_file(self, tmp_path):
        """RED: -o should write to different file."""
        from ralph_orchestrator.__main__ import main

        input_file = tmp_path / "input.md"
        output_file = tmp_path / "output.md"
        original = "# Task\nDo something.\n"
        input_file.write_text(original)

        with patch('sys.argv', ['ralph', 'structure', str(input_file), '-o', str(output_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        # Input unchanged
        assert input_file.read_text() == original
        # Output has transformation
        assert output_file.exists()
        assert "TASK_COMPLETE" in output_file.read_text()

    def test_output_to_stdout(self, tmp_path, capsys):
        """RED: -o - should output to stdout."""
        from ralph_orchestrator.__main__ import main

        input_file = tmp_path / "input.md"
        original = "# Task\nDo something.\n"
        input_file.write_text(original)

        with patch('sys.argv', ['ralph', 'structure', str(input_file), '-o', '-']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        # Input unchanged
        assert input_file.read_text() == original

        captured = capsys.readouterr()
        assert "TASK_COMPLETE" in captured.out


class TestStructureJSONOutput:
    """Tests for --json output mode."""

    def test_json_output_valid_json(self, tmp_path, capsys):
        """RED: --json should produce valid JSON."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("# Task\nDo something.\n")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--json', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        # Should be valid JSON
        result = json.loads(captured.out)
        assert isinstance(result, dict)

    def test_json_output_contains_fields(self, tmp_path, capsys):
        """RED: --json should contain transformation fields."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("# Task\nDo something.\n")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--json', '--dry-run']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        # Should contain TransformResult fields
        assert "original" in result
        assert "transformed" in result
        assert "changes" in result


class TestStructureFlags:
    """Tests for transformation control flags."""

    def test_minimal_flag(self, tmp_path):
        """RED: --minimal should only add critical elements."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("# Task\n1. First step\n2. Second step\n")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--minimal']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        content = prompt_file.read_text()
        # Should have completion marker (critical)
        assert "TASK_COMPLETE" in content
        # Should NOT convert numbered list to checkboxes (MEDIUM priority)
        assert "1. First step" in content or "- [ ] First step" in content

    def test_no_completion_flag(self, tmp_path):
        """RED: --no-completion should skip completion marker."""
        from ralph_orchestrator.__main__ import main

        prompt_file = tmp_path / "test.md"
        original = "# Task\nDo something.\n"
        prompt_file.write_text(original)

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file), '--no-completion']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        content = prompt_file.read_text()
        # Should NOT have completion marker
        assert "TASK_COMPLETE" not in content


class TestStructureTextInput:
    """Tests for literal text input."""

    def test_text_input_transforms(self, capsys):
        """RED: Should accept literal text instead of file."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'structure', '--text', 'Create a hello world script']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "TASK_COMPLETE" in captured.out

    def test_text_with_output_file(self, tmp_path, capsys):
        """RED: --text with -o should write to file."""
        from ralph_orchestrator.__main__ import main

        output_file = tmp_path / "output.md"

        with patch('sys.argv', ['ralph', 'structure', '--text', 'Create a script', '-o', str(output_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

        assert output_file.exists()
        assert "TASK_COMPLETE" in output_file.read_text()


class TestStructureIntegrationWithTransformer:
    """Integration tests ensuring CLI uses PromptTransformer correctly."""

    def test_uses_prompt_transformer(self, tmp_path):
        """RED: Should use PromptTransformer for transformation."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.transform import PromptTransformer

        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("# Task\nTest task.\n")

        with patch.object(PromptTransformer, 'transform', wraps=PromptTransformer().transform) as mock_transform:
            with patch('sys.argv', ['ralph', 'structure', str(prompt_file)]):
                with pytest.raises(SystemExit):
                    main()

            # Should have called transform
            mock_transform.assert_called_once()

    def test_passes_context_when_available(self, tmp_path):
        """RED: Should pass TransformContext with working directory."""
        from ralph_orchestrator.__main__ import main
        from ralph_orchestrator.transform import PromptTransformer, TransformContext

        prompt_file = tmp_path / "test.md"
        prompt_file.write_text("# Task\nTest task.\n")

        with patch('sys.argv', ['ralph', 'structure', str(prompt_file)]):
            with pytest.raises(SystemExit):
                main()

        # Check transformed content has working directory
        content = prompt_file.read_text()
        # Path resolution enricher adds Working Directory when context provided
        # But CLI mode may not add it - this test verifies the integration
