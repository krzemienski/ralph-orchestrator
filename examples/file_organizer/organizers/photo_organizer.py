"""Photo organizer module for organizing photos by date taken."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

from .base import BaseOrganizer

logger = logging.getLogger(__name__)


# Common photo file extensions (lowercase)
PHOTO_EXTENSIONS: Set[str] = {
    # Standard image formats
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    # Apple formats
    ".heic",
    ".heif",
    # RAW formats
    ".raw",
    ".cr2",  # Canon
    ".nef",  # Nikon
    ".arw",  # Sony
    ".orf",  # Olympus
    ".rw2",  # Panasonic
    ".dng",  # Adobe Digital Negative
}


# Common date patterns in filenames
FILENAME_DATE_PATTERNS = [
    # ISO format: 2024-03-15
    (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),
    # Compact format: 20240315
    (r"(\d{4})(\d{2})(\d{2})", "%Y%m%d"),
    # Underscore format: 2024_03_15
    (r"(\d{4})_(\d{2})_(\d{2})", "%Y_%m_%d"),
]


class PhotoOrganizer(BaseOrganizer):
    """Organizes photos by date taken.

    Photos are organized into Year/Month folders based on:
    1. EXIF DateTimeOriginal tag (preferred)
    2. EXIF DateTime tag (fallback)
    3. Date from filename patterns
    4. File modification time (last resort)
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        dry_run: bool = False,
        date_format: str = "%Y/%m",
    ) -> None:
        """Initialize the photo organizer.

        Args:
            source_dir: Directory containing photos to organize.
            target_dir: Directory where organized photos will be placed.
            dry_run: If True, preview changes without moving files.
            date_format: Format string for date-based folder structure.
                Default is "%Y/%m" which creates Year/Month folders.
        """
        super().__init__(source_dir, target_dir, dry_run)
        self.date_format = date_format

    def get_target_path(self, file_path: Path) -> Path:
        """Determine the target path for a photo file.

        Photos are organized into folders by date taken.
        For example: photo.jpg taken 2024-03-15 -> target_dir/2024/03/photo.jpg

        Args:
            file_path: Path to the source file.

        Returns:
            The target path where the file should be moved.
        """
        # Try to get date from various sources
        date_taken = self._get_date_from_exif(file_path)

        if date_taken is None:
            date_taken = self._get_date_from_filename(file_path)

        if date_taken is None:
            # Fall back to file modification time
            date_taken = datetime.fromtimestamp(file_path.stat().st_mtime)
            logger.debug(f"Using mtime for {file_path.name}: {date_taken}")

        # Create folder path based on date format
        folder_path = date_taken.strftime(self.date_format)

        return self.target_dir / folder_path / file_path.name

    def should_organize(self, file_path: Path) -> bool:
        """Determine if a file should be organized.

        Only organizes files with photo extensions.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file is a photo that should be organized.
        """
        if not file_path.is_file():
            return False

        extension = file_path.suffix.lower()
        return extension in PHOTO_EXTENSIONS

    def _get_date_from_exif(self, file_path: Path) -> Optional[datetime]:
        """Extract date from EXIF metadata.

        Args:
            file_path: Path to the image file.

        Returns:
            datetime if EXIF date found, None otherwise.
        """
        if not PIL_AVAILABLE:
            logger.debug("PIL not available, skipping EXIF extraction")
            return None

        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()

                if exif_data is None:
                    return None

                # EXIF tag 36867 = DateTimeOriginal (preferred)
                # EXIF tag 306 = DateTime (fallback)
                for tag_id in [36867, 306]:
                    if tag_id in exif_data:
                        date_str = exif_data[tag_id]
                        try:
                            # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            logger.debug(f"Could not parse EXIF date: {date_str}")
                            continue

        except Exception as e:
            logger.debug(f"Could not read EXIF from {file_path}: {e}")

        return None

    def _get_date_from_filename(self, file_path: Path) -> Optional[datetime]:
        """Extract date from filename patterns.

        Supports patterns like:
        - 2024-03-15_photo.jpg (ISO format)
        - IMG_20240315_143000.jpg (compact format)
        - 2024_03_15_vacation.jpg (underscore format)

        Args:
            file_path: Path to the file.

        Returns:
            datetime if date found in filename, None otherwise.
        """
        filename = file_path.stem

        for pattern, date_format in FILENAME_DATE_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                try:
                    date_str = "".join(match.groups())
                    # Normalize to compact format for parsing
                    date_str_compact = re.sub(r"[-_]", "", date_str)
                    return datetime.strptime(date_str_compact, "%Y%m%d")
                except ValueError:
                    continue

        return None
