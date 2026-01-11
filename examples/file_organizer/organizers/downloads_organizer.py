"""Downloads organizer module for cleaning up downloads folder."""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from .base import BaseOrganizer

logger = logging.getLogger(__name__)


# Default number of days after which files are considered old
DEFAULT_ARCHIVE_DAYS = 30

# Default mapping of file extensions to folder names
DEFAULT_FILE_TYPE_MAPPING: Dict[str, str] = {
    # Documents
    "pdf": "documents",
    "doc": "documents",
    "docx": "documents",
    "txt": "documents",
    "rtf": "documents",
    "odt": "documents",
    "xls": "documents",
    "xlsx": "documents",
    "csv": "documents",
    "ppt": "documents",
    "pptx": "documents",
    # Archives
    "zip": "archives",
    "tar": "archives",
    "gz": "archives",
    "rar": "archives",
    "7z": "archives",
    "bz2": "archives",
    "xz": "archives",
    # Installers
    "dmg": "installers",
    "pkg": "installers",
    "exe": "installers",
    "msi": "installers",
    "app": "installers",
    "deb": "installers",
    "rpm": "installers",
    # Images
    "jpg": "images",
    "jpeg": "images",
    "png": "images",
    "gif": "images",
    "bmp": "images",
    "svg": "images",
    "webp": "images",
    "ico": "images",
    # Videos
    "mp4": "videos",
    "mkv": "videos",
    "avi": "videos",
    "mov": "videos",
    "wmv": "videos",
    "flv": "videos",
    "webm": "videos",
    # Audio
    "mp3": "audio",
    "wav": "audio",
    "flac": "audio",
    "aac": "audio",
    "ogg": "audio",
    "m4a": "audio",
    # Code/Scripts
    "py": "code",
    "js": "code",
    "ts": "code",
    "html": "code",
    "css": "code",
    "json": "code",
    "xml": "code",
    "yaml": "code",
    "yml": "code",
    "sh": "code",
}


class DownloadsOrganizer(BaseOrganizer):
    """Organizer for downloads folder.

    Organizes files by type and archives old files.
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        dry_run: bool = False,
        archive_days: int = DEFAULT_ARCHIVE_DAYS,
        file_type_mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the downloads organizer.

        Args:
            source_dir: Downloads directory to organize.
            target_dir: Directory where organized files will be placed.
            dry_run: If True, preview changes without moving files.
            archive_days: Number of days after which files are archived.
            file_type_mapping: Custom mapping of extensions to folders.
        """
        super().__init__(source_dir, target_dir, dry_run)
        self.archive_days = archive_days
        self.file_type_mapping = (
            file_type_mapping if file_type_mapping is not None
            else DEFAULT_FILE_TYPE_MAPPING
        )

    def should_organize(self, file_path: Path) -> bool:
        """Determine if a file should be organized.

        Skips directories and hidden files.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file should be organized.
        """
        # Must be a file
        if not file_path.is_file():
            return False

        # Skip hidden files
        if file_path.name.startswith("."):
            return False

        return True

    def is_old_file(self, file_path: Path) -> bool:
        """Check if a file is older than archive_days.

        Args:
            file_path: Path to the file.

        Returns:
            True if file modification time is older than archive_days.
        """
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        cutoff = datetime.now() - timedelta(days=self.archive_days)
        return mtime < cutoff

    def get_file_type_folder(self, file_path: Path) -> str:
        """Get the folder name for a file based on its extension.

        Args:
            file_path: Path to the file.

        Returns:
            Folder name for the file type (e.g., "documents", "archives").
        """
        extension = file_path.suffix.lower().lstrip(".")
        return self.file_type_mapping.get(extension, "misc")

    def get_target_path(self, file_path: Path) -> Path:
        """Determine the target path for a file.

        Old files go to archive/type folder, recent files to type folder.

        Args:
            file_path: Path to the source file.

        Returns:
            The target path where the file should be moved.
        """
        type_folder = self.get_file_type_folder(file_path)

        if self.is_old_file(file_path):
            # Archive old files
            return self.target_dir / "archive" / type_folder / file_path.name
        else:
            # Regular organization by type
            return self.target_dir / type_folder / file_path.name
