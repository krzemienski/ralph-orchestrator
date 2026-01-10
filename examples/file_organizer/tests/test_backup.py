"""Tests for backup module."""

import os
import tempfile
import stat
from pathlib import Path
from datetime import datetime
import pytest

# Import will fail until we implement the module
from utils.backup import BackupManager, BackupError


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_create_backup_of_single_file(self, tmp_path):
        """Should create a backup copy of a file."""
        # Create a source file
        source_file = tmp_path / "source" / "test.txt"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("test content")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        assert backup_path.exists()
        assert backup_path.read_text() == "test content"
        # Original file should still exist
        assert source_file.exists()

    def test_backup_creates_timestamped_directory(self, tmp_path):
        """Should create a timestamped backup directory."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("test content")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        # Check backup is in a timestamped directory
        # Format: YYYY-MM-DD_HHMMSS
        assert backup_path.parent.parent == backup_dir
        # The parent directory should match timestamp pattern
        parent_name = backup_path.parent.name
        assert len(parent_name) == 17  # YYYY-MM-DD_HHMMSS

    def test_backup_preserves_directory_structure(self, tmp_path):
        """Should preserve relative directory structure in backup."""
        # Create nested source structure
        source_dir = tmp_path / "source"
        source_file = source_dir / "subdir" / "nested" / "file.txt"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("nested content")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir, source_base=source_dir)

        backup_path = manager.backup_file(source_file)

        # Should preserve structure: backups/TIMESTAMP/subdir/nested/file.txt
        assert "subdir" in str(backup_path)
        assert "nested" in str(backup_path)
        assert backup_path.name == "file.txt"

    def test_backup_preserves_file_permissions(self, tmp_path):
        """Should preserve file permissions in backup."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("test content")

        # Set specific permissions (e.g., read-only)
        original_mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
        os.chmod(source_file, original_mode)

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        # Verify permissions are preserved
        backup_mode = os.stat(backup_path).st_mode & 0o777
        assert backup_mode == original_mode

    def test_backup_multiple_files(self, tmp_path):
        """Should backup multiple files in same session."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        file1 = source_dir / "file1.txt"
        file2 = source_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir, source_base=source_dir)

        backup1 = manager.backup_file(file1)
        backup2 = manager.backup_file(file2)

        # Both backups should be in the same session directory
        assert backup1.parent == backup2.parent
        assert backup1.read_text() == "content 1"
        assert backup2.read_text() == "content 2"

    def test_backup_nonexistent_file_raises_error(self, tmp_path):
        """Should raise BackupError when source file doesn't exist."""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        with pytest.raises(BackupError) as exc_info:
            manager.backup_file(tmp_path / "nonexistent.txt")

        assert "does not exist" in str(exc_info.value)

    def test_backup_directory_created_automatically(self, tmp_path):
        """Should create backup directory if it doesn't exist."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("test content")

        backup_dir = tmp_path / "new" / "nested" / "backup"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        assert backup_dir.exists()
        assert backup_path.exists()

    def test_get_backup_manifest(self, tmp_path):
        """Should return list of backed up files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        file1 = source_dir / "file1.txt"
        file2 = source_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir, source_base=source_dir)

        manager.backup_file(file1)
        manager.backup_file(file2)

        manifest = manager.get_manifest()

        assert len(manifest) == 2
        assert any(item["source"] == str(file1) for item in manifest)
        assert any(item["source"] == str(file2) for item in manifest)

    def test_restore_file_from_backup(self, tmp_path):
        """Should restore file from backup."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("original content")

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        # Modify or delete the original
        source_file.write_text("modified content")

        # Restore from backup
        manager.restore_file(backup_path, source_file)

        assert source_file.read_text() == "original content"

    def test_restore_preserves_permissions(self, tmp_path):
        """Should preserve permissions when restoring."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("content")

        original_mode = stat.S_IRWXU | stat.S_IRGRP
        os.chmod(source_file, original_mode)

        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=backup_dir)

        backup_path = manager.backup_file(source_file)

        # Change permissions on original
        os.chmod(source_file, stat.S_IRUSR)

        # Restore
        manager.restore_file(backup_path, source_file)

        restored_mode = os.stat(source_file).st_mode & 0o777
        assert restored_mode == original_mode

    def test_default_backup_directory(self):
        """Should use ~/.file_organizer_backups as default."""
        manager = BackupManager()

        expected = Path.home() / ".file_organizer_backups"
        assert manager.backup_dir == expected

    def test_session_id_consistent_within_session(self, tmp_path):
        """Should use consistent session ID for all backups in one session."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        file1 = source_dir / "a.txt"
        file2 = source_dir / "b.txt"
        file1.write_text("a")
        file2.write_text("b")

        manager = BackupManager(backup_dir=tmp_path / "backups")

        b1 = manager.backup_file(file1)
        b2 = manager.backup_file(file2)

        # Same session directory
        assert b1.parent == b2.parent

    def test_new_session_creates_new_directory(self, tmp_path):
        """New BackupManager instance should create new session directory."""
        source_file = tmp_path / "test.txt"
        source_file.write_text("content")

        backup_dir = tmp_path / "backups"
        manager1 = BackupManager(backup_dir=backup_dir)
        backup1 = manager1.backup_file(source_file)

        # Force a new session
        manager2 = BackupManager(backup_dir=backup_dir)
        manager2._session_id = None  # Reset session
        backup2 = manager2.backup_file(source_file)

        # Different session directories
        assert backup1.parent != backup2.parent
