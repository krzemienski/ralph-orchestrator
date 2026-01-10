"""Tests for the base organizer class."""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

from organizers.base import BaseOrganizer, OrganizationResult


class ConcreteOrganizer(BaseOrganizer):
    """Concrete implementation for testing."""

    def get_target_path(self, file_path: Path) -> Path:
        """Move all files to 'organized' subfolder."""
        return self.target_dir / "organized" / file_path.name


class TestBaseOrganizer:
    """Tests for BaseOrganizer class."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary source and target directories."""
        source = tempfile.mkdtemp()
        target = tempfile.mkdtemp()
        yield Path(source), Path(target)
        shutil.rmtree(source, ignore_errors=True)
        shutil.rmtree(target, ignore_errors=True)

    @pytest.fixture
    def organizer(self, temp_dirs):
        """Create a concrete organizer instance."""
        source, target = temp_dirs
        return ConcreteOrganizer(source_dir=source, target_dir=target)

    def test_organizer_initialization(self, temp_dirs):
        """Test that organizer initializes with source and target directories."""
        source, target = temp_dirs
        organizer = ConcreteOrganizer(source_dir=source, target_dir=target)

        assert organizer.source_dir == source
        assert organizer.target_dir == target
        assert organizer.dry_run is False

    def test_organizer_dry_run_mode(self, temp_dirs):
        """Test that organizer can be initialized in dry-run mode."""
        source, target = temp_dirs
        organizer = ConcreteOrganizer(source_dir=source, target_dir=target, dry_run=True)

        assert organizer.dry_run is True

    def test_organize_moves_file(self, organizer, temp_dirs):
        """Test that organize() moves a file to the target location."""
        source, target = temp_dirs

        # Create a test file
        test_file = source / "test.txt"
        test_file.write_text("test content")

        result = organizer.organize()

        assert result.files_moved == 1
        assert result.files_skipped == 0
        assert result.errors == []
        assert (target / "organized" / "test.txt").exists()
        assert not test_file.exists()  # Original should be gone

    def test_organize_dry_run_does_not_move(self, temp_dirs):
        """Test that dry-run mode previews but doesn't move files."""
        source, target = temp_dirs
        organizer = ConcreteOrganizer(source_dir=source, target_dir=target, dry_run=True)

        # Create a test file
        test_file = source / "test.txt"
        test_file.write_text("test content")

        result = organizer.organize()

        assert result.files_moved == 0
        assert result.files_would_move == 1
        assert test_file.exists()  # Original should still be there
        assert not (target / "organized" / "test.txt").exists()

    def test_organize_preserves_file_permissions(self, organizer, temp_dirs):
        """Test that file permissions are preserved after move."""
        source, target = temp_dirs

        # Create a test file with specific permissions
        test_file = source / "executable.sh"
        test_file.write_text("#!/bin/bash\necho hello")
        os.chmod(test_file, 0o755)

        organizer.organize()

        moved_file = target / "organized" / "executable.sh"
        assert moved_file.exists()
        assert os.stat(moved_file).st_mode & 0o777 == 0o755

    def test_organize_handles_duplicate_filenames(self, organizer, temp_dirs):
        """Test that duplicate filenames are handled safely."""
        source, target = temp_dirs

        # Create a test file
        test_file = source / "test.txt"
        test_file.write_text("original content")

        # Pre-create a file with the same name in target
        organized_dir = target / "organized"
        organized_dir.mkdir(parents=True)
        existing_file = organized_dir / "test.txt"
        existing_file.write_text("existing content")

        result = organizer.organize()

        # Should have created a renamed copy
        assert result.files_moved == 1
        # Original target file should be unchanged
        assert existing_file.read_text() == "existing content"
        # New file should exist with modified name
        files_in_target = list(organized_dir.glob("test*.txt"))
        assert len(files_in_target) == 2

    def test_organize_result_contains_actions(self, organizer, temp_dirs):
        """Test that OrganizationResult contains action details for undo."""
        source, target = temp_dirs

        test_file = source / "test.txt"
        test_file.write_text("test content")

        result = organizer.organize()

        assert len(result.actions) == 1
        action = result.actions[0]
        assert action["type"] == "move"
        assert "source" in action
        assert "destination" in action

    def test_organize_empty_directory(self, organizer):
        """Test organizing an empty directory."""
        result = organizer.organize()

        assert result.files_moved == 0
        assert result.files_skipped == 0
        assert result.errors == []

    def test_organize_creates_target_subdirectories(self, organizer, temp_dirs):
        """Test that target subdirectories are created as needed."""
        source, target = temp_dirs

        test_file = source / "test.txt"
        test_file.write_text("test content")

        # Target 'organized' folder doesn't exist yet
        assert not (target / "organized").exists()

        organizer.organize()

        assert (target / "organized").exists()
        assert (target / "organized" / "test.txt").exists()
