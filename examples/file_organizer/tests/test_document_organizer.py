"""Tests for document organizer module."""

import os
import tempfile
from pathlib import Path

import pytest

from organizers.document_organizer import DocumentOrganizer


class TestDocumentOrganizer:
    """Tests for DocumentOrganizer class."""

    @pytest.fixture
    def temp_source(self) -> Path:
        """Create a temporary source directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()

            # Create test files with various extensions
            (source / "report.pdf").write_text("PDF content")
            (source / "letter.docx").write_text("DOCX content")
            (source / "notes.txt").write_text("TXT content")
            (source / "data.xlsx").write_text("XLSX content")
            (source / "image.jpg").write_text("Not a document")

            yield source

    @pytest.fixture
    def temp_target(self) -> Path:
        """Create a temporary target directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "target"
            target.mkdir()
            yield target

    @pytest.fixture
    def source_and_target(self):
        """Create both source and target directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            # Create test files
            (source / "report.pdf").write_text("PDF content")
            (source / "letter.docx").write_text("DOCX content")
            (source / "notes.txt").write_text("TXT content")
            (source / "data.xlsx").write_text("XLSX content")
            (source / "image.jpg").write_text("Not a document")

            yield source, target

    def test_initialization(self, source_and_target):
        """Test DocumentOrganizer initialization."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        assert organizer.source_dir == source
        assert organizer.target_dir == target
        assert organizer.dry_run is False

    def test_initialization_with_dry_run(self, source_and_target):
        """Test initialization with dry-run mode."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target, dry_run=True)

        assert organizer.dry_run is True

    def test_initialization_with_custom_extensions(self, source_and_target):
        """Test initialization with custom extensions."""
        source, target = source_and_target
        custom_extensions = {".pdf": "pdfs", ".doc": "docs"}

        organizer = DocumentOrganizer(
            source, target, extensions=custom_extensions
        )

        assert organizer.extensions == custom_extensions

    def test_default_extensions(self, source_and_target):
        """Test that default extensions are set correctly."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        # Check common document extensions are included
        assert ".pdf" in organizer.extensions
        assert ".docx" in organizer.extensions
        assert ".txt" in organizer.extensions
        assert ".xlsx" in organizer.extensions
        assert ".doc" in organizer.extensions

    def test_get_target_path_pdf(self, source_and_target):
        """Test target path for PDF files."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        pdf_file = source / "report.pdf"
        target_path = organizer.get_target_path(pdf_file)

        assert target_path == target / "pdf" / "report.pdf"

    def test_get_target_path_docx(self, source_and_target):
        """Test target path for DOCX files."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        docx_file = source / "letter.docx"
        target_path = organizer.get_target_path(docx_file)

        assert target_path == target / "docx" / "letter.docx"

    def test_get_target_path_txt(self, source_and_target):
        """Test target path for TXT files."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        txt_file = source / "notes.txt"
        target_path = organizer.get_target_path(txt_file)

        assert target_path == target / "txt" / "notes.txt"

    def test_get_target_path_custom_folder(self, source_and_target):
        """Test target path with custom folder names."""
        source, target = source_and_target
        custom_extensions = {
            ".pdf": "documents/pdfs",
            ".txt": "text_files",
        }

        organizer = DocumentOrganizer(
            source, target, extensions=custom_extensions
        )

        pdf_file = source / "report.pdf"
        target_path = organizer.get_target_path(pdf_file)

        assert target_path == target / "documents/pdfs" / "report.pdf"

    def test_should_organize_document_files(self, source_and_target):
        """Test that document files should be organized."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        assert organizer.should_organize(source / "report.pdf") is True
        assert organizer.should_organize(source / "letter.docx") is True
        assert organizer.should_organize(source / "notes.txt") is True

    def test_should_not_organize_non_document_files(self, source_and_target):
        """Test that non-document files should not be organized."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        # Image files should not be organized
        assert organizer.should_organize(source / "image.jpg") is False

    def test_organize_dry_run(self, source_and_target):
        """Test dry-run mode doesn't move files."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target, dry_run=True)

        result = organizer.organize()

        # Files should still be in source
        assert (source / "report.pdf").exists()
        assert (source / "letter.docx").exists()
        assert (source / "notes.txt").exists()

        # Target should be empty
        assert not (target / "pdf").exists()

        # Dry-run count should be correct
        # Only pdf, docx, txt, xlsx are documents (4 files), not jpg
        assert result.files_would_move == 4

    def test_organize_moves_files(self, source_and_target):
        """Test that organize actually moves document files."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        result = organizer.organize()

        # Files should be moved to appropriate folders
        assert (target / "pdf" / "report.pdf").exists()
        assert (target / "docx" / "letter.docx").exists()
        assert (target / "txt" / "notes.txt").exists()
        assert (target / "xlsx" / "data.xlsx").exists()

        # Non-document file should remain in source
        assert (source / "image.jpg").exists()

        # Check result counts
        assert result.files_moved == 4
        assert len(result.errors) == 0

    def test_organize_preserves_permissions(self, source_and_target):
        """Test that file permissions are preserved."""
        source, target = source_and_target

        # Set specific permissions on source file
        test_file = source / "report.pdf"
        os.chmod(test_file, 0o644)

        organizer = DocumentOrganizer(source, target)
        organizer.organize()

        # Check permissions on moved file
        moved_file = target / "pdf" / "report.pdf"
        mode = os.stat(moved_file).st_mode & 0o777
        assert mode == 0o644

    def test_organize_handles_subdirectories(self):
        """Test organizing files from subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            target = Path(tmpdir) / "target"
            source.mkdir()
            target.mkdir()

            # Create nested structure
            subdir = source / "subdir"
            subdir.mkdir()
            (subdir / "nested.pdf").write_text("Nested PDF")

            organizer = DocumentOrganizer(source, target)
            result = organizer.organize()

            # Nested file should be organized
            assert (target / "pdf" / "nested.pdf").exists()
            assert result.files_moved == 1

    def test_organize_records_actions(self, source_and_target):
        """Test that organization actions are recorded for undo."""
        source, target = source_and_target
        organizer = DocumentOrganizer(source, target)

        result = organizer.organize()

        # Should have actions recorded
        assert len(result.actions) == 4

        # Check action structure
        action = result.actions[0]
        assert "type" in action
        assert "source" in action
        assert "destination" in action
        assert action["type"] == "move"
