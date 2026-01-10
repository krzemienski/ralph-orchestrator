"""Backup management for file organizer."""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Raised when there is an error with backup operations."""

    pass


class BackupManager:
    """Manages file backups before organization operations.

    Creates timestamped backup directories and preserves file permissions.
    Supports restoring files from backup.
    """

    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        source_base: Optional[Path] = None,
    ) -> None:
        """Initialize the backup manager.

        Args:
            backup_dir: Directory where backups will be stored.
                If None, uses ~/.file_organizer_backups
            source_base: Base directory for preserving relative paths.
                If None, files are backed up without directory structure.
        """
        if backup_dir is None:
            self.backup_dir = Path.home() / ".file_organizer_backups"
        else:
            self.backup_dir = Path(backup_dir)

        self.source_base = Path(source_base) if source_base else None
        self._session_id: Optional[str] = None
        self._manifest: List[Dict[str, Any]] = []

    @property
    def session_dir(self) -> Path:
        """Get the session-specific backup directory.

        Creates a new timestamped directory for each backup session.
        """
        if self._session_id is None:
            self._session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        return self.backup_dir / self._session_id

    def backup_file(self, source_path: Path) -> Path:
        """Create a backup of a file.

        Args:
            source_path: Path to the file to backup.

        Returns:
            Path to the backup file.

        Raises:
            BackupError: If the source file doesn't exist or backup fails.
        """
        source_path = Path(source_path)

        if not source_path.exists():
            raise BackupError(f"Source file does not exist: {source_path}")

        if not source_path.is_file():
            raise BackupError(f"Source is not a file: {source_path}")

        # Determine backup path
        if self.source_base and source_path.is_relative_to(self.source_base):
            # Preserve relative directory structure
            relative_path = source_path.relative_to(self.source_base)
            backup_path = self.session_dir / relative_path
        else:
            # Just use filename
            backup_path = self.session_dir / source_path.name

        try:
            # Create backup directory structure
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Get original permissions
            original_mode = os.stat(source_path).st_mode

            # Copy the file
            shutil.copy2(str(source_path), str(backup_path))

            # Ensure permissions are preserved
            os.chmod(backup_path, original_mode & 0o777)

            # Record in manifest
            self._manifest.append({
                "source": str(source_path),
                "backup": str(backup_path),
                "timestamp": datetime.now().isoformat(),
                "permissions": original_mode & 0o777,
            })

            logger.info(f"Backed up: {source_path} -> {backup_path}")
            return backup_path

        except OSError as e:
            raise BackupError(f"Failed to backup {source_path}: {e}")

    def restore_file(self, backup_path: Path, target_path: Path) -> None:
        """Restore a file from backup.

        Args:
            backup_path: Path to the backup file.
            target_path: Path where the file should be restored.

        Raises:
            BackupError: If restoration fails.
        """
        backup_path = Path(backup_path)
        target_path = Path(target_path)

        if not backup_path.exists():
            raise BackupError(f"Backup file does not exist: {backup_path}")

        try:
            # Get permissions from backup
            backup_mode = os.stat(backup_path).st_mode

            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(str(backup_path), str(target_path))

            # Restore permissions
            os.chmod(target_path, backup_mode & 0o777)

            logger.info(f"Restored: {backup_path} -> {target_path}")

        except OSError as e:
            raise BackupError(f"Failed to restore {backup_path}: {e}")

    def get_manifest(self) -> List[Dict[str, Any]]:
        """Get the manifest of backed up files.

        Returns:
            List of dictionaries with source, backup, timestamp, and permissions.
        """
        return self._manifest.copy()

    def __repr__(self) -> str:
        """Return string representation of the backup manager."""
        return f"BackupManager(backup_dir={self.backup_dir})"
