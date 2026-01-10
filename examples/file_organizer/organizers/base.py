"""Base organizer class for file organization."""

import os
import shutil
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OrganizationResult:
    """Result of an organization operation."""

    files_moved: int = 0
    files_skipped: int = 0
    files_would_move: int = 0  # For dry-run mode
    errors: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def add_action(self, action_type: str, source: Path, destination: Path) -> None:
        """Record an action for potential undo."""
        self.actions.append({
            "type": action_type,
            "source": str(source),
            "destination": str(destination),
        })


class BaseOrganizer(ABC):
    """Abstract base class for file organizers.

    Subclasses must implement get_target_path() to define
    how files should be organized.
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        dry_run: bool = False,
    ) -> None:
        """Initialize the organizer.

        Args:
            source_dir: Directory containing files to organize.
            target_dir: Directory where organized files will be placed.
            dry_run: If True, preview changes without moving files.
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run

    @abstractmethod
    def get_target_path(self, file_path: Path) -> Path:
        """Determine the target path for a file.

        Args:
            file_path: Path to the source file.

        Returns:
            The target path where the file should be moved.
        """
        pass

    def should_organize(self, file_path: Path) -> bool:
        """Determine if a file should be organized.

        Override in subclasses to filter files.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file should be organized.
        """
        return file_path.is_file()

    def get_unique_path(self, target_path: Path) -> Path:
        """Generate a unique path if target already exists.

        Args:
            target_path: The desired target path.

        Returns:
            A unique path that doesn't conflict with existing files.
        """
        if not target_path.exists():
            return target_path

        # Generate unique filename
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def organize(self) -> OrganizationResult:
        """Organize files from source to target directory.

        Returns:
            OrganizationResult with details of the operation.
        """
        result = OrganizationResult()

        # Iterate through all files in source directory
        for file_path in self.source_dir.rglob("*"):
            if not self.should_organize(file_path):
                continue

            try:
                target_path = self.get_target_path(file_path)
                target_path = self.get_unique_path(target_path)

                if self.dry_run:
                    result.files_would_move += 1
                    logger.info(f"Would move: {file_path} -> {target_path}")
                else:
                    self._move_file(file_path, target_path)
                    result.files_moved += 1
                    result.add_action("move", file_path, target_path)
                    logger.info(f"Moved: {file_path} -> {target_path}")

            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                result.errors.append(error_msg)
                logger.error(error_msg)

        return result

    def _move_file(self, source: Path, destination: Path) -> None:
        """Move a file, preserving permissions.

        Args:
            source: Source file path.
            destination: Destination file path.
        """
        # Create target directory if it doesn't exist
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Get original permissions
        original_mode = os.stat(source).st_mode

        # Move the file
        shutil.move(str(source), str(destination))

        # Restore permissions
        os.chmod(destination, original_mode)
