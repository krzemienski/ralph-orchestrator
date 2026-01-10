"""Configuration management for file organizer."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when there is an error with the configuration."""

    pass


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "dry_run": False,
    "create_backup": True,
    "log_level": "INFO",
    "log_file": None,
}


class Config:
    """Configuration manager for file organizer.

    Loads configuration from a YAML file and provides access to settings.
    Uses ~/.file_organizer.yml as the default configuration file.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file.
                If None, uses ~/.file_organizer.yml
        """
        if config_path is None:
            self.config_path = Path.home() / ".file_organizer.yml"
        else:
            self.config_path = Path(config_path)

        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self) -> None:
        """Load configuration from the YAML file."""
        if not self.config_path.exists():
            logger.debug(f"Config file not found at {self.config_path}, using defaults")
            return

        try:
            with open(self.config_path, "r") as f:
                loaded_config = yaml.safe_load(f)

            if loaded_config:
                self._config.update(loaded_config)
                logger.debug(f"Loaded configuration from {self.config_path}")

        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: The configuration key to retrieve.
            default: Default value if key is not found.

        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: The configuration key.
            value: The value to set.
        """
        self._config[key] = value

    def save(self) -> None:
        """Save the current configuration to the YAML file."""
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w") as f:
                yaml.dump(self._config, f, default_flow_style=False)

            logger.debug(f"Saved configuration to {self.config_path}")

        except IOError as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    def expand_path(self, path: str) -> Path:
        """Expand ~ and environment variables in a path.

        Args:
            path: The path string to expand.

        Returns:
            Expanded Path object.
        """
        return Path(path).expanduser()

    def __repr__(self) -> str:
        """Return string representation of the config."""
        return f"Config(config_path={self.config_path})"
