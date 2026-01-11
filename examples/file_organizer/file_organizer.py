#!/usr/bin/env python3
"""File Organizer CLI - Organize files by type, date, and custom rules.

Usage:
    file_organizer photos --source ~/Pictures [--target ~/Organized/Photos] [--dry-run]
    file_organizer documents --source ~/Documents [--target ~/Organized/Documents]
    file_organizer downloads --source ~/Downloads [--target ~/Organized/Downloads]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from organizers import DocumentOrganizer, PhotoOrganizer, DownloadsOrganizer
from utils.config import Config, ConfigError
from utils.backup import BackupManager

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="file_organizer",
        description="Organize files by type, date, and custom rules.",
        epilog="Examples:\n"
        "  file_organizer photos --source ~/Pictures --dry-run\n"
        "  file_organizer documents --source ~/Documents --target ~/Organized\n"
        "  file_organizer downloads --source ~/Downloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Organization command")

    # Common arguments for all commands
    def add_common_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--source",
            required=True,
            help="Source directory containing files to organize",
        )
        subparser.add_argument(
            "--target",
            default=None,
            help="Target directory for organized files (default: source directory)",
        )
        subparser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview changes without moving files",
        )
        subparser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose (DEBUG) logging",
        )
        subparser.add_argument(
            "--config",
            "-c",
            default=None,
            help="Path to configuration file (default: ~/.file_organizer.yml)",
        )
        subparser.add_argument(
            "--no-backup",
            action="store_true",
            dest="no_backup",
            help="Skip creating backups before moving files",
        )

    # Photos command
    photos_parser = subparsers.add_parser(
        "photos",
        help="Organize photos by date taken (EXIF data)",
    )
    add_common_args(photos_parser)

    # Documents command
    documents_parser = subparsers.add_parser(
        "documents",
        help="Organize documents by file extension",
    )
    add_common_args(documents_parser)

    # Downloads command
    downloads_parser = subparsers.add_parser(
        "downloads",
        help="Organize downloads by file type (archive old files)",
    )
    add_common_args(downloads_parser)

    return parser


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG.
        log_file: Path to log file. If None, logs to stderr only.
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def run_command(args: argparse.Namespace) -> int:
    """Execute the organization command.

    Args:
        args: Parsed command line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Load configuration
    try:
        config = Config(args.config) if args.config else Config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Validate source directory
    source_path = Path(args.source).expanduser()
    if not source_path.exists():
        logger.error(f"Source directory does not exist: {source_path}")
        return 1

    if not source_path.is_dir():
        logger.error(f"Source is not a directory: {source_path}")
        return 1

    # Determine target directory
    if args.target:
        target_path = Path(args.target).expanduser()
    else:
        target_path = source_path

    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)

    # Set up backup manager if needed
    backup_manager = None
    if not args.no_backup and not args.dry_run:
        backup_manager = BackupManager(source_base=source_path)
        logger.info(f"Backups will be saved to: {backup_manager.backup_dir}")

    # Select and run the appropriate organizer
    try:
        if args.command == "photos":
            organizer = PhotoOrganizer(
                source_dir=source_path,
                target_dir=target_path,
                dry_run=args.dry_run,
            )
        elif args.command == "documents":
            organizer = DocumentOrganizer(
                source_dir=source_path,
                target_dir=target_path,
                dry_run=args.dry_run,
            )
        elif args.command == "downloads":
            organizer = DownloadsOrganizer(
                source_dir=source_path,
                target_dir=target_path,
                dry_run=args.dry_run,
            )
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

        # Run organization
        logger.info(f"Organizing {args.command} from {source_path} to {target_path}")
        if args.dry_run:
            logger.info("DRY RUN - No files will be moved")

        result = organizer.organize()

        # Report results
        if args.dry_run:
            logger.info(f"Would move {result.files_would_move} files")
        else:
            logger.info(f"Moved {result.files_moved} files")

        if result.files_skipped:
            logger.info(f"Skipped {result.files_skipped} files")

        if result.errors:
            logger.warning(f"Encountered {len(result.errors)} errors:")
            for error in result.errors:
                logger.warning(f"  - {error}")

        return 0

    except Exception as e:
        logger.error(f"Organization failed: {e}")
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Check if a command was provided
    if args.command is None:
        parser.print_help()
        return 0

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Run the command
    return run_command(args)


if __name__ == "__main__":
    sys.exit(main())
