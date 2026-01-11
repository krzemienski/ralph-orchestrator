"""Tests for DownloadsOrganizer module."""

import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from organizers.downloads_organizer import (
    DownloadsOrganizer,
    DEFAULT_FILE_TYPE_MAPPING,
    DEFAULT_ARCHIVE_DAYS,
)


class TestDownloadsOrganizerConstants:
    """Tests for module constants."""

    def test_default_file_type_mapping_has_common_types(self):
        """Default mapping should include common download types."""
        assert "pdf" in DEFAULT_FILE_TYPE_MAPPING
        assert "zip" in DEFAULT_FILE_TYPE_MAPPING
        assert "dmg" in DEFAULT_FILE_TYPE_MAPPING
        assert "exe" in DEFAULT_FILE_TYPE_MAPPING

    def test_default_archive_days_is_reasonable(self):
        """Default archive days should be 30."""
        assert DEFAULT_ARCHIVE_DAYS == 30


class TestDownloadsOrganizerInit:
    """Tests for DownloadsOrganizer initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Initialize with default settings."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)

        assert organizer.source_dir == source
        assert organizer.target_dir == target
        assert organizer.dry_run is False
        assert organizer.archive_days == DEFAULT_ARCHIVE_DAYS
        assert organizer.file_type_mapping == DEFAULT_FILE_TYPE_MAPPING

    def test_init_with_dry_run(self, tmp_path):
        """Initialize with dry-run mode."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target, dry_run=True)

        assert organizer.dry_run is True

    def test_init_with_custom_archive_days(self, tmp_path):
        """Initialize with custom archive days."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target, archive_days=60)

        assert organizer.archive_days == 60

    def test_init_with_custom_file_type_mapping(self, tmp_path):
        """Initialize with custom file type mapping."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        custom_mapping = {"py": "scripts", "js": "scripts"}
        organizer = DownloadsOrganizer(source, target, file_type_mapping=custom_mapping)

        assert organizer.file_type_mapping == custom_mapping


class TestDownloadsOrganizerShouldOrganize:
    """Tests for should_organize method."""

    def test_should_organize_regular_file(self, tmp_path):
        """Regular files should be organized."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "document.pdf"
        test_file.touch()

        organizer = DownloadsOrganizer(source, target)
        assert organizer.should_organize(test_file) is True

    def test_should_not_organize_directory(self, tmp_path):
        """Directories should not be organized."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_dir = source / "subfolder"
        test_dir.mkdir()

        organizer = DownloadsOrganizer(source, target)
        assert organizer.should_organize(test_dir) is False

    def test_should_not_organize_hidden_files(self, tmp_path):
        """Hidden files (starting with .) should not be organized."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        hidden_file = source / ".DS_Store"
        hidden_file.touch()

        organizer = DownloadsOrganizer(source, target)
        assert organizer.should_organize(hidden_file) is False


class TestDownloadsOrganizerIsOldFile:
    """Tests for is_old_file method."""

    def test_is_old_file_recent(self, tmp_path):
        """Recently modified files should not be old."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "recent.pdf"
        test_file.touch()  # Creates with current timestamp

        organizer = DownloadsOrganizer(source, target, archive_days=30)
        assert organizer.is_old_file(test_file) is False

    def test_is_old_file_old(self, tmp_path):
        """Files older than archive_days should be old."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "old.pdf"
        test_file.touch()

        # Set modification time to 45 days ago
        old_time = (datetime.now() - timedelta(days=45)).timestamp()
        os.utime(test_file, (old_time, old_time))

        organizer = DownloadsOrganizer(source, target, archive_days=30)
        assert organizer.is_old_file(test_file) is True


class TestDownloadsOrganizerGetFileTypeFolder:
    """Tests for get_file_type_folder method."""

    def test_get_folder_for_pdf(self, tmp_path):
        """PDF files go to documents folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)
        folder = organizer.get_file_type_folder(Path("test.pdf"))

        assert folder == "documents"

    def test_get_folder_for_zip(self, tmp_path):
        """ZIP files go to archives folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)
        folder = organizer.get_file_type_folder(Path("test.zip"))

        assert folder == "archives"

    def test_get_folder_for_dmg(self, tmp_path):
        """DMG files go to installers folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)
        folder = organizer.get_file_type_folder(Path("app.dmg"))

        assert folder == "installers"

    def test_get_folder_for_unknown_extension(self, tmp_path):
        """Unknown extensions go to misc folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)
        folder = organizer.get_file_type_folder(Path("test.xyz123"))

        assert folder == "misc"

    def test_get_folder_case_insensitive(self, tmp_path):
        """Extension matching should be case-insensitive."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        organizer = DownloadsOrganizer(source, target)
        folder = organizer.get_file_type_folder(Path("TEST.PDF"))

        assert folder == "documents"


class TestDownloadsOrganizerGetTargetPath:
    """Tests for get_target_path method."""

    def test_get_target_path_recent_file(self, tmp_path):
        """Recent files go to type-based folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "document.pdf"
        test_file.touch()

        organizer = DownloadsOrganizer(source, target)
        result = organizer.get_target_path(test_file)

        assert result == target / "documents" / "document.pdf"

    def test_get_target_path_old_file(self, tmp_path):
        """Old files go to archive/type folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "old_document.pdf"
        test_file.touch()

        # Set modification time to 45 days ago
        old_time = (datetime.now() - timedelta(days=45)).timestamp()
        os.utime(test_file, (old_time, old_time))

        organizer = DownloadsOrganizer(source, target, archive_days=30)
        result = organizer.get_target_path(test_file)

        assert result == target / "archive" / "documents" / "old_document.pdf"


class TestDownloadsOrganizerOrganize:
    """Tests for organize method."""

    def test_organize_in_dry_run_mode(self, tmp_path):
        """Dry-run mode should not move files."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        # Create test files
        (source / "test.pdf").touch()
        (source / "test.zip").touch()

        organizer = DownloadsOrganizer(source, target, dry_run=True)
        result = organizer.organize()

        assert result.files_would_move == 2
        assert result.files_moved == 0
        assert (source / "test.pdf").exists()
        assert (source / "test.zip").exists()

    def test_organize_moves_files_by_type(self, tmp_path):
        """Files should be organized by type."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        # Create test files
        (source / "doc.pdf").write_text("pdf content")
        (source / "archive.zip").write_text("zip content")

        organizer = DownloadsOrganizer(source, target)
        result = organizer.organize()

        assert result.files_moved == 2
        assert (target / "documents" / "doc.pdf").exists()
        assert (target / "archives" / "archive.zip").exists()

    def test_organize_archives_old_files(self, tmp_path):
        """Old files should go to archive folder."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        # Create old file
        old_file = source / "old.pdf"
        old_file.write_text("old content")
        old_time = (datetime.now() - timedelta(days=45)).timestamp()
        os.utime(old_file, (old_time, old_time))

        organizer = DownloadsOrganizer(source, target, archive_days=30)
        result = organizer.organize()

        assert result.files_moved == 1
        assert (target / "archive" / "documents" / "old.pdf").exists()

    def test_organize_skips_hidden_files(self, tmp_path):
        """Hidden files should be skipped."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        # Create files
        (source / "visible.pdf").touch()
        (source / ".hidden").touch()

        organizer = DownloadsOrganizer(source, target)
        result = organizer.organize()

        assert result.files_moved == 1
        assert (source / ".hidden").exists()  # Not moved

    def test_organize_records_actions(self, tmp_path):
        """Actions should be recorded for undo."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        (source / "test.pdf").touch()

        organizer = DownloadsOrganizer(source, target)
        result = organizer.organize()

        assert len(result.actions) == 1
        assert result.actions[0]["type"] == "move"
        assert "test.pdf" in result.actions[0]["source"]

    def test_organize_preserves_permissions(self, tmp_path):
        """File permissions should be preserved."""
        source = tmp_path / "downloads"
        target = tmp_path / "organized"
        source.mkdir()

        test_file = source / "script.sh"
        test_file.touch()
        os.chmod(test_file, 0o755)

        organizer = DownloadsOrganizer(source, target)
        result = organizer.organize()

        assert result.files_moved == 1
        # .sh files go to "code" folder per DEFAULT_FILE_TYPE_MAPPING
        moved_file = target / "code" / "script.sh"
        assert moved_file.exists()
        assert os.stat(moved_file).st_mode & 0o777 == 0o755
