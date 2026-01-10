# CLI Tool Example

Create a Python CLI tool for file organization:

## Requirements

1. Command-line interface using argparse
2. Commands:
   - `organize photos` - Organize photos by date taken
   - `organize documents` - Sort documents by type
   - `organize downloads` - Clean up downloads folder
   - `organize --custom <pattern>` - Custom organization rules

3. Features:
   - Dry-run mode to preview changes
   - Undo functionality
   - Progress bar for large operations
   - Configuration file support (~/.file_organizer.yml)
   - Logging to file

4. Organization rules:
   - Photos: Year/Month folders based on EXIF data
   - Documents: Folders by extension (pdf/, docx/, txt/)
   - Downloads: Archive old files, group by type
   - Custom: User-defined patterns

5. Safety:
   - Never delete files
   - Create backups before moving
   - Handle duplicate filenames
   - Preserve file permissions

Save as file_organizer.py with supporting modules:
- organizers/photo_organizer.py
- organizers/document_organizer.py
- utils/config.py
- utils/backup.py

Include requirements.txt with dependencies

The orchestrator will continue iterations until all components are implemented and tested

---

## Progress Tracking

### Iteration 1 - COMPLETE
**Task:** Create project structure and base organizer class

**Completed:**
- [x] Created project structure: `examples/file_organizer/{organizers,utils,tests}`
- [x] Implemented `organizers/base.py` with:
  - `OrganizationResult` dataclass for tracking results
  - `BaseOrganizer` abstract base class
  - Support for dry-run mode
  - Duplicate filename handling
  - File permission preservation
  - Action recording for undo functionality
- [x] Wrote TDD tests (9 passing tests)

**Next iteration:** Implement utils/config.py

### Iteration 2 - COMPLETE
**Task:** Implement configuration management module

**Completed:**
- [x] Implemented `utils/config.py` with:
  - `Config` class for YAML configuration management
  - `ConfigError` exception for error handling
  - Default configuration values (dry_run, create_backup, log_level)
  - Support for loading from `~/.file_organizer.yml`
  - Photo organization settings (source_dir, target_dir, date_format)
  - Document organization settings (extensions list)
  - Custom rules configuration support
  - Save functionality to persist config changes
  - Path expansion for ~ home directory
- [x] Wrote TDD tests (11 passing tests)
- [x] Total tests: 20 passing

**Next iteration:** Implement utils/backup.py
