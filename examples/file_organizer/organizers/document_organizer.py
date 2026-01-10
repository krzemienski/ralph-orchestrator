"""Document organizer module for sorting documents by type."""

import logging
from pathlib import Path
from typing import Dict, Optional

from .base import BaseOrganizer

logger = logging.getLogger(__name__)


# Default document extensions and their target folder names
DEFAULT_DOCUMENT_EXTENSIONS: Dict[str, str] = {
    # Text documents
    ".txt": "txt",
    ".md": "txt",
    ".rtf": "txt",
    # Word documents
    ".doc": "doc",
    ".docx": "docx",
    ".odt": "doc",
    # Spreadsheets
    ".xls": "xls",
    ".xlsx": "xlsx",
    ".csv": "csv",
    ".ods": "spreadsheet",
    # Presentations
    ".ppt": "ppt",
    ".pptx": "pptx",
    ".odp": "presentation",
    # PDF
    ".pdf": "pdf",
    # Other documents
    ".epub": "ebook",
    ".mobi": "ebook",
}


class DocumentOrganizer(BaseOrganizer):
    """Organizes documents by file extension.

    Sorts document files into folders based on their extension type.
    For example: .pdf files go into pdf/, .docx files go into docx/.
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        dry_run: bool = False,
        extensions: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the document organizer.

        Args:
            source_dir: Directory containing documents to organize.
            target_dir: Directory where organized documents will be placed.
            dry_run: If True, preview changes without moving files.
            extensions: Custom mapping of extensions to folder names.
                If None, uses default document extensions.
        """
        super().__init__(source_dir, target_dir, dry_run)

        if extensions is not None:
            self.extensions = extensions
        else:
            self.extensions = DEFAULT_DOCUMENT_EXTENSIONS.copy()

    def get_target_path(self, file_path: Path) -> Path:
        """Determine the target path for a document file.

        Documents are organized into folders by their extension.
        For example: report.pdf -> target_dir/pdf/report.pdf

        Args:
            file_path: Path to the source file.

        Returns:
            The target path where the file should be moved.
        """
        extension = file_path.suffix.lower()
        folder_name = self.extensions.get(extension, extension.lstrip("."))

        return self.target_dir / folder_name / file_path.name

    def should_organize(self, file_path: Path) -> bool:
        """Determine if a file should be organized.

        Only organizes files with document extensions.

        Args:
            file_path: Path to the file.

        Returns:
            True if the file is a document that should be organized.
        """
        if not file_path.is_file():
            return False

        extension = file_path.suffix.lower()
        return extension in self.extensions
