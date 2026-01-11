# Organizers package
from .base import BaseOrganizer, OrganizationResult
from .document_organizer import DocumentOrganizer
from .photo_organizer import PhotoOrganizer, PHOTO_EXTENSIONS
from .downloads_organizer import (
    DownloadsOrganizer,
    DEFAULT_FILE_TYPE_MAPPING,
    DEFAULT_ARCHIVE_DAYS,
)

__all__ = [
    "BaseOrganizer",
    "OrganizationResult",
    "DocumentOrganizer",
    "PhotoOrganizer",
    "PHOTO_EXTENSIONS",
    "DownloadsOrganizer",
    "DEFAULT_FILE_TYPE_MAPPING",
    "DEFAULT_ARCHIVE_DAYS",
]
