"""Tests for the photo organizer module."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from organizers.photo_organizer import PhotoOrganizer, PHOTO_EXTENSIONS


class TestPhotoExtensions:
    """Tests for photo extension constants."""

    def test_photo_extensions_contains_common_formats(self):
        """Should include common photo file extensions."""
        assert ".jpg" in PHOTO_EXTENSIONS
        assert ".jpeg" in PHOTO_EXTENSIONS
        assert ".png" in PHOTO_EXTENSIONS
        assert ".gif" in PHOTO_EXTENSIONS
        assert ".bmp" in PHOTO_EXTENSIONS
        assert ".tiff" in PHOTO_EXTENSIONS
        assert ".heic" in PHOTO_EXTENSIONS
        assert ".webp" in PHOTO_EXTENSIONS

    def test_photo_extensions_contains_raw_formats(self):
        """Should include common RAW photo formats."""
        assert ".raw" in PHOTO_EXTENSIONS
        assert ".cr2" in PHOTO_EXTENSIONS
        assert ".nef" in PHOTO_EXTENSIONS
        assert ".arw" in PHOTO_EXTENSIONS


class TestPhotoOrganizerInit:
    """Tests for PhotoOrganizer initialization."""

    def test_init_with_default_date_format(self):
        """Should use default date format when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            organizer = PhotoOrganizer(source, target)

            assert organizer.date_format == "%Y/%m"

    def test_init_with_custom_date_format(self):
        """Should use custom date format when specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            organizer = PhotoOrganizer(source, target, date_format="%Y-%m-%d")

            assert organizer.date_format == "%Y-%m-%d"

    def test_init_with_dry_run(self):
        """Should set dry_run mode correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            organizer = PhotoOrganizer(source, target, dry_run=True)

            assert organizer.dry_run is True


class TestPhotoOrganizerShouldOrganize:
    """Tests for PhotoOrganizer.should_organize method."""

    def test_should_organize_jpg(self):
        """Should organize .jpg files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "test.jpg"
            photo.write_bytes(b"fake image data")

            organizer = PhotoOrganizer(source, target)

            assert organizer.should_organize(photo) is True

    def test_should_organize_png(self):
        """Should organize .png files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "test.png"
            photo.write_bytes(b"fake image data")

            organizer = PhotoOrganizer(source, target)

            assert organizer.should_organize(photo) is True

    def test_should_organize_heic(self):
        """Should organize .heic files (iPhone photos)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "test.HEIC"
            photo.write_bytes(b"fake image data")

            organizer = PhotoOrganizer(source, target)

            assert organizer.should_organize(photo) is True

    def test_should_not_organize_non_photo(self):
        """Should not organize non-photo files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            doc = source / "test.pdf"
            doc.write_bytes(b"fake pdf data")

            organizer = PhotoOrganizer(source, target)

            assert organizer.should_organize(doc) is False

    def test_should_not_organize_directory(self):
        """Should not organize directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            subdir = source / "photos"
            subdir.mkdir()

            organizer = PhotoOrganizer(source, target)

            assert organizer.should_organize(subdir) is False


class TestPhotoOrganizerGetDateFromExif:
    """Tests for PhotoOrganizer._get_date_from_exif method."""

    def test_get_date_from_exif_no_exif(self):
        """Should return None when file has no EXIF data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            # Create a minimal JPEG without EXIF
            photo = source / "no_exif.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target)

            assert organizer._get_date_from_exif(photo) is None

    @patch("organizers.photo_organizer.Image")
    def test_get_date_from_exif_with_datetime_original(self, mock_image_module):
        """Should extract date from EXIF DateTimeOriginal tag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "with_exif.jpg"
            photo.write_bytes(b"fake image data")

            # Mock EXIF data - tag 36867 is DateTimeOriginal
            mock_img = MagicMock()
            mock_exif = {36867: "2024:03:15 14:30:00"}
            mock_img._getexif.return_value = mock_exif
            mock_image_module.open.return_value.__enter__.return_value = mock_img

            organizer = PhotoOrganizer(source, target)
            result = organizer._get_date_from_exif(photo)

            assert result == datetime(2024, 3, 15, 14, 30, 0)

    @patch("organizers.photo_organizer.Image")
    def test_get_date_from_exif_with_datetime(self, mock_image_module):
        """Should fall back to DateTime tag if DateTimeOriginal not present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "with_exif.jpg"
            photo.write_bytes(b"fake image data")

            # Mock EXIF data - tag 306 is DateTime
            mock_img = MagicMock()
            mock_exif = {306: "2024:06:20 10:00:00"}
            mock_img._getexif.return_value = mock_exif
            mock_image_module.open.return_value.__enter__.return_value = mock_img

            organizer = PhotoOrganizer(source, target)
            result = organizer._get_date_from_exif(photo)

            assert result == datetime(2024, 6, 20, 10, 0, 0)


class TestPhotoOrganizerGetDateFromFilename:
    """Tests for PhotoOrganizer._get_date_from_filename method."""

    def test_get_date_from_filename_iso_format(self):
        """Should parse ISO date format from filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "2024-03-15_photo.jpg"
            photo.write_bytes(b"fake")

            organizer = PhotoOrganizer(source, target)
            result = organizer._get_date_from_filename(photo)

            assert result.year == 2024
            assert result.month == 3
            assert result.day == 15

    def test_get_date_from_filename_compact_format(self):
        """Should parse compact date format from filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "IMG_20240315_143000.jpg"
            photo.write_bytes(b"fake")

            organizer = PhotoOrganizer(source, target)
            result = organizer._get_date_from_filename(photo)

            assert result.year == 2024
            assert result.month == 3
            assert result.day == 15

    def test_get_date_from_filename_no_date(self):
        """Should return None when filename has no date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "vacation_photo.jpg"
            photo.write_bytes(b"fake")

            organizer = PhotoOrganizer(source, target)
            result = organizer._get_date_from_filename(photo)

            assert result is None


class TestPhotoOrganizerGetTargetPath:
    """Tests for PhotoOrganizer.get_target_path method."""

    @patch("organizers.photo_organizer.Image")
    def test_get_target_path_with_exif_date(self, mock_image_module):
        """Should use EXIF date for target path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "photo.jpg"
            photo.write_bytes(b"fake image data")

            # Mock EXIF date
            mock_img = MagicMock()
            mock_exif = {36867: "2024:03:15 14:30:00"}
            mock_img._getexif.return_value = mock_exif
            mock_image_module.open.return_value.__enter__.return_value = mock_img

            organizer = PhotoOrganizer(source, target)
            result = organizer.get_target_path(photo)

            assert result == target / "2024" / "03" / "photo.jpg"

    def test_get_target_path_with_filename_date(self):
        """Should use filename date when no EXIF data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "IMG_20240620_143000.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target)
            result = organizer.get_target_path(photo)

            assert result == target / "2024" / "06" / "IMG_20240620_143000.jpg"

    def test_get_target_path_fallback_to_mtime(self):
        """Should use file modification time as fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "unknown.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target)
            result = organizer.get_target_path(photo)

            # Should use current file modification time
            mtime = datetime.fromtimestamp(photo.stat().st_mtime)
            expected_folder = mtime.strftime("%Y/%m").split("/")
            assert result.parent.parent.name == expected_folder[0]  # Year
            assert result.parent.name == expected_folder[1]  # Month

    def test_get_target_path_with_custom_format(self):
        """Should use custom date format for folder structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()

            photo = source / "2024-12-25_christmas.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target, date_format="%Y-%m-%d")
            result = organizer.get_target_path(photo)

            assert result == target / "2024-12-25" / "2024-12-25_christmas.jpg"


class TestPhotoOrganizerOrganize:
    """Tests for PhotoOrganizer.organize method."""

    def test_organize_in_dry_run_mode(self):
        """Should preview changes without moving files in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            # Create test photo with date in filename
            photo = source / "IMG_20240315_143000.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target, dry_run=True)
            result = organizer.organize()

            assert result.files_would_move == 1
            assert result.files_moved == 0
            assert photo.exists()  # File should still be in source

    def test_organize_moves_photos(self):
        """Should move photos to date-based folders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            # Create test photo with date in filename
            photo = source / "IMG_20240315_143000.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target, dry_run=False)
            result = organizer.organize()

            assert result.files_moved == 1
            assert not photo.exists()  # File should be moved
            assert (target / "2024" / "03" / "IMG_20240315_143000.jpg").exists()

    def test_organize_skips_non_photos(self):
        """Should skip non-photo files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            # Create a non-photo file
            doc = source / "document.pdf"
            doc.write_bytes(b"fake pdf data")

            organizer = PhotoOrganizer(source, target, dry_run=False)
            result = organizer.organize()

            assert result.files_moved == 0
            assert doc.exists()  # PDF should remain

    def test_organize_records_actions(self):
        """Should record move actions for undo functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            photo = source / "IMG_20240315_143000.jpg"
            photo.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9")

            organizer = PhotoOrganizer(source, target, dry_run=False)
            result = organizer.organize()

            assert len(result.actions) == 1
            assert result.actions[0]["type"] == "move"
            assert "IMG_20240315_143000.jpg" in result.actions[0]["source"]
