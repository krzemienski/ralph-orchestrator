"""Tests for the CLI interface."""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest


class TestCLIArgumentParsing:
    """Test command line argument parsing."""

    def test_organize_photos_command(self):
        """Test 'organize photos' command creates correct arguments."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp/photos"])

        assert args.command == "photos"
        assert args.source == "/tmp/photos"

    def test_organize_documents_command(self):
        """Test 'organize documents' command creates correct arguments."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["documents", "--source", "/tmp/docs"])

        assert args.command == "documents"
        assert args.source == "/tmp/docs"

    def test_organize_downloads_command(self):
        """Test 'organize downloads' command creates correct arguments."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["downloads", "--source", "/tmp/downloads"])

        assert args.command == "downloads"
        assert args.source == "/tmp/downloads"

    def test_dry_run_flag(self):
        """Test --dry-run flag is parsed correctly."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp", "--dry-run"])

        assert args.dry_run is True

    def test_no_dry_run_by_default(self):
        """Test dry-run is False by default."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp"])

        assert args.dry_run is False

    def test_target_directory_option(self):
        """Test --target option for destination directory."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp", "--target", "/organized"])

        assert args.target == "/organized"

    def test_verbose_flag(self):
        """Test --verbose flag for debug logging."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp", "--verbose"])

        assert args.verbose is True

    def test_config_option(self):
        """Test --config option for custom config file."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["photos", "--source", "/tmp", "--config", "/path/to/config.yml"]
        )

        assert args.config == "/path/to/config.yml"

    def test_no_backup_flag(self):
        """Test --no-backup flag to skip backup creation."""
        from file_organizer import create_parser

        parser = create_parser()
        args = parser.parse_args(["photos", "--source", "/tmp", "--no-backup"])

        assert args.no_backup is True

    def test_source_is_required(self):
        """Test that --source is required for organization commands."""
        from file_organizer import create_parser

        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["photos"])


class TestCLIPhotoOrganization:
    """Test photo organization through CLI."""

    def test_run_photos_dry_run(self, tmp_path):
        """Test photos command in dry-run mode."""
        from file_organizer import run_command

        # Create source directory with a fake photo
        source = tmp_path / "source"
        source.mkdir()
        photo = source / "photo.jpg"
        photo.write_text("fake photo")

        target = tmp_path / "target"

        args = argparse.Namespace(
            command="photos",
            source=str(source),
            target=str(target),
            dry_run=True,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 0
        # File should still be in source (dry run)
        assert photo.exists()

    def test_run_photos_moves_files(self, tmp_path):
        """Test photos command moves files."""
        from file_organizer import run_command

        # Create source directory with a fake photo
        source = tmp_path / "source"
        source.mkdir()
        photo = source / "photo.jpg"
        photo.write_text("fake photo")

        target = tmp_path / "target"

        args = argparse.Namespace(
            command="photos",
            source=str(source),
            target=str(target),
            dry_run=False,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 0
        # File should be moved from source
        assert not photo.exists()


class TestCLIDocumentOrganization:
    """Test document organization through CLI."""

    def test_run_documents_dry_run(self, tmp_path):
        """Test documents command in dry-run mode."""
        from file_organizer import run_command

        source = tmp_path / "source"
        source.mkdir()
        doc = source / "report.pdf"
        doc.write_text("fake pdf")

        target = tmp_path / "target"

        args = argparse.Namespace(
            command="documents",
            source=str(source),
            target=str(target),
            dry_run=True,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 0
        # File should still be in source (dry run)
        assert doc.exists()

    def test_run_documents_organizes_by_extension(self, tmp_path):
        """Test documents command organizes by extension."""
        from file_organizer import run_command

        source = tmp_path / "source"
        source.mkdir()
        doc = source / "report.pdf"
        doc.write_text("fake pdf")

        target = tmp_path / "target"

        args = argparse.Namespace(
            command="documents",
            source=str(source),
            target=str(target),
            dry_run=False,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 0
        # File should be in pdf folder
        organized_file = target / "pdf" / "report.pdf"
        assert organized_file.exists()


class TestCLIDownloadsOrganization:
    """Test downloads organization through CLI."""

    def test_run_downloads_dry_run(self, tmp_path):
        """Test downloads command in dry-run mode."""
        from file_organizer import run_command

        source = tmp_path / "source"
        source.mkdir()
        installer = source / "app.dmg"
        installer.write_text("fake dmg")

        target = tmp_path / "target"

        args = argparse.Namespace(
            command="downloads",
            source=str(source),
            target=str(target),
            dry_run=True,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 0
        # File should still be in source (dry run)
        assert installer.exists()


class TestCLILogging:
    """Test CLI logging functionality."""

    def test_verbose_enables_debug_logging(self, tmp_path, caplog):
        """Test --verbose flag enables DEBUG logging level."""
        from file_organizer import setup_logging

        # Create a temporary log file
        log_file = tmp_path / "test.log"

        setup_logging(verbose=True, log_file=str(log_file))

        import logging

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_default_logging_is_info(self, tmp_path):
        """Test default logging level is INFO."""
        from file_organizer import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(verbose=False, log_file=str(log_file))

        import logging

        logger = logging.getLogger()
        assert logger.level == logging.INFO


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_source_returns_error(self, tmp_path):
        """Test error when source directory doesn't exist."""
        from file_organizer import run_command

        args = argparse.Namespace(
            command="photos",
            source="/nonexistent/path",
            target=str(tmp_path / "target"),
            dry_run=False,
            verbose=False,
            config=None,
            no_backup=True,
        )

        result = run_command(args)

        assert result == 1  # Error code

    def test_invalid_config_returns_error(self, tmp_path):
        """Test error when config file is invalid."""
        from file_organizer import run_command

        source = tmp_path / "source"
        source.mkdir()

        # Create invalid config
        config_file = tmp_path / "invalid.yml"
        config_file.write_text("invalid: yaml: content: [")

        args = argparse.Namespace(
            command="photos",
            source=str(source),
            target=str(tmp_path / "target"),
            dry_run=False,
            verbose=False,
            config=str(config_file),
            no_backup=True,
        )

        result = run_command(args)

        assert result == 1  # Error code


class TestCLIMainEntry:
    """Test main entry point."""

    def test_main_returns_zero_on_success(self, tmp_path):
        """Test main() returns 0 on success."""
        from file_organizer import main

        source = tmp_path / "source"
        source.mkdir()

        target = tmp_path / "target"

        with mock.patch(
            "sys.argv",
            ["file_organizer", "photos", "--source", str(source), "--target", str(target), "--dry-run"],
        ):
            result = main()
            assert result == 0
