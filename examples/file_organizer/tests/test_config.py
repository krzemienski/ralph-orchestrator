"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path
import pytest

# Import will fail until we implement the module
from utils.config import Config, ConfigError


class TestConfig:
    """Tests for Config class."""

    def test_load_default_config_when_no_file_exists(self):
        """Should return default configuration when no config file exists."""
        config = Config(config_path="/nonexistent/path/.file_organizer.yml")

        assert config.get("dry_run") is False
        assert config.get("create_backup") is True
        assert config.get("log_level") == "INFO"

    def test_load_config_from_yaml_file(self, tmp_path):
        """Should load configuration from YAML file."""
        config_content = """
dry_run: true
create_backup: false
log_level: DEBUG
log_file: /tmp/organizer.log
"""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text(config_content)

        config = Config(config_path=str(config_file))

        assert config.get("dry_run") is True
        assert config.get("create_backup") is False
        assert config.get("log_level") == "DEBUG"
        assert config.get("log_file") == "/tmp/organizer.log"

    def test_get_returns_none_for_missing_key(self, tmp_path):
        """Should return None for missing keys by default."""
        config = Config(config_path="/nonexistent/path")

        assert config.get("nonexistent_key") is None

    def test_get_returns_default_for_missing_key(self):
        """Should return provided default for missing keys."""
        config = Config(config_path="/nonexistent/path")

        assert config.get("nonexistent_key", "default_value") == "default_value"

    def test_photo_organization_config(self, tmp_path):
        """Should support photo organization settings."""
        config_content = """
photos:
  source_dir: ~/Pictures
  target_dir: ~/Pictures/Organized
  date_format: "%Y/%m"
"""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text(config_content)

        config = Config(config_path=str(config_file))

        photos_config = config.get("photos")
        assert photos_config["source_dir"] == "~/Pictures"
        assert photos_config["target_dir"] == "~/Pictures/Organized"
        assert photos_config["date_format"] == "%Y/%m"

    def test_document_organization_config(self, tmp_path):
        """Should support document organization settings."""
        config_content = """
documents:
  source_dir: ~/Documents
  target_dir: ~/Documents/Organized
  extensions:
    - pdf
    - docx
    - txt
"""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text(config_content)

        config = Config(config_path=str(config_file))

        docs_config = config.get("documents")
        assert docs_config["source_dir"] == "~/Documents"
        assert docs_config["extensions"] == ["pdf", "docx", "txt"]

    def test_custom_rules_config(self, tmp_path):
        """Should support custom organization rules."""
        config_content = """
custom_rules:
  - name: work_projects
    pattern: "*.pptx"
    target: ~/Work/Presentations
  - name: receipts
    pattern: "receipt_*.pdf"
    target: ~/Finance/Receipts
"""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text(config_content)

        config = Config(config_path=str(config_file))

        rules = config.get("custom_rules")
        assert len(rules) == 2
        assert rules[0]["name"] == "work_projects"
        assert rules[0]["pattern"] == "*.pptx"
        assert rules[1]["target"] == "~/Finance/Receipts"

    def test_save_config(self, tmp_path):
        """Should save configuration to YAML file."""
        config_file = tmp_path / ".file_organizer.yml"
        config = Config(config_path=str(config_file))

        config.set("dry_run", True)
        config.set("log_level", "DEBUG")
        config.save()

        # Reload and verify
        reloaded = Config(config_path=str(config_file))
        assert reloaded.get("dry_run") is True
        assert reloaded.get("log_level") == "DEBUG"

    def test_invalid_yaml_raises_config_error(self, tmp_path):
        """Should raise ConfigError for invalid YAML."""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text("invalid: yaml: syntax: [")

        with pytest.raises(ConfigError):
            Config(config_path=str(config_file))

    def test_expand_home_directory(self, tmp_path):
        """Should expand ~ in paths."""
        config_content = """
photos:
  source_dir: ~/Pictures
"""
        config_file = tmp_path / ".file_organizer.yml"
        config_file.write_text(config_content)

        config = Config(config_path=str(config_file))

        expanded = config.expand_path("~/Pictures")
        assert expanded == Path.home() / "Pictures"

    def test_default_config_path_is_home_directory(self):
        """Should use ~/.file_organizer.yml as default path."""
        config = Config()

        expected_path = Path.home() / ".file_organizer.yml"
        assert config.config_path == expected_path
