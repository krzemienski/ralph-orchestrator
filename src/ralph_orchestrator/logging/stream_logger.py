# ABOUTME: Real-time structured log streaming for Ralph Orchestrator
# ABOUTME: Outputs to console, file, and named pipe (FIFO) simultaneously

"""
Real-time structured log streaming for Ralph Orchestrator.
Outputs to console, file, and named pipe simultaneously.

Features:
- Structured JSON log entries with timestamps and metadata
- Multi-output streaming (console, file, FIFO pipe)
- Thread-safe logging with locking
- Rich-formatted console output with color coding
- Callback registration for custom handlers
"""

import os
import json
import stat
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List, Any, Dict
from dataclasses import dataclass, asdict, field
from enum import IntEnum


class LogLevel(IntEnum):
    """Log level enumeration matching Python logging levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class StructuredLogEntry:
    """
    Structured log entry for JSON serialization and Rich formatting.

    Attributes:
        timestamp: ISO format timestamp
        level: Log level name (DEBUG, INFO, WARNING, ERROR)
        component: Source component name (e.g., 'orchestrator', 'adapter', 'learning')
        message: Human-readable log message
        iteration: Current iteration number (if applicable)
        context_tokens: Current context window token usage (if tracked)
        metadata: Additional structured data
    """
    timestamp: str
    level: str
    component: str
    message: str
    iteration: Optional[int] = None
    context_tokens: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Serialize entry to JSON string."""
        data = asdict(self)
        # Remove None values for cleaner output
        data = {k: v for k, v in data.items() if v is not None}
        return json.dumps(data, default=str)

    def to_rich(self) -> str:
        """Format entry for Rich console output with color coding."""
        level_styles = {
            "DEBUG": "[dim cyan]",
            "INFO": "[blue]",
            "WARNING": "[yellow]",
            "ERROR": "[red bold]",
            "CRITICAL": "[white on red bold]"
        }
        style = level_styles.get(self.level, "")
        end_style = "[/]" if style else ""

        # Build context suffix
        context_parts = []
        if self.iteration is not None:
            context_parts.append(f"iter={self.iteration}")
        if self.context_tokens is not None:
            context_parts.append(f"tokens={self.context_tokens:,}")
        context_suffix = f" ({', '.join(context_parts)})" if context_parts else ""

        # Short timestamp for console
        short_ts = self.timestamp.split("T")[1].split(".")[0] if "T" in self.timestamp else self.timestamp[-8:]

        return f"{style}[{short_ts}] [{self.level:7}] {self.component}: {self.message}{context_suffix}{end_style}"

    def to_plain(self) -> str:
        """Format entry as plain text without Rich markup."""
        context_parts = []
        if self.iteration is not None:
            context_parts.append(f"iter={self.iteration}")
        if self.context_tokens is not None:
            context_parts.append(f"tokens={self.context_tokens:,}")
        context_suffix = f" ({', '.join(context_parts)})" if context_parts else ""

        short_ts = self.timestamp.split("T")[1].split(".")[0] if "T" in self.timestamp else self.timestamp[-8:]
        return f"[{short_ts}] [{self.level:7}] {self.component}: {self.message}{context_suffix}"


class StreamLogger:
    """
    Multiplexed log streaming to console, file, and FIFO pipe.

    This logger outputs structured log entries to multiple destinations:
    - Console (stderr): Rich-formatted with colors
    - Log file: JSON Lines format for machine parsing
    - FIFO pipe: JSON for real-time consumption by external tools

    Thread-safe with locking for concurrent access.

    Example:
        logger = StreamLogger(log_level=LogLevel.DEBUG)
        logger.info("orchestrator", "Starting orchestration loop")
        logger.debug("adapter", "Sending prompt", iteration=1, tokens=1500)
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_fifo: bool = True,
        session_id: Optional[str] = None
    ):
        """
        Initialize StreamLogger with configurable outputs.

        Args:
            log_dir: Directory for log files (default: .agent/logs)
            log_level: Minimum log level to output
            enable_console: Output to stderr with Rich formatting
            enable_file: Output to JSONL file
            enable_fifo: Output to named pipe for real-time streaming
            session_id: Optional session identifier for log file naming
        """
        # Find repository root
        if log_dir is None:
            current_dir = Path.cwd()
            repo_root = current_dir
            while repo_root.parent != repo_root:
                if (repo_root / ".git").exists():
                    break
                repo_root = repo_root.parent
            log_dir = repo_root / ".agent" / "logs"

        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_fifo = enable_fifo
        self._callbacks: List[Callable[[StructuredLogEntry], None]] = []
        self._fifo_path: Optional[Path] = None
        self._log_file: Optional[Path] = None
        self._lock = threading.RLock()
        self._closed = False
        self._console = None

        # Session identification
        self._session_id = session_id or datetime.now().strftime("%Y%m%d-%H%M%S")

        self._setup()

    def _setup(self):
        """Initialize log outputs (directory, file, FIFO pipe)."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup Rich console for stderr output
        if self.enable_console:
            try:
                from rich.console import Console
                self._console = Console(stderr=True, force_terminal=True)
            except ImportError:
                self._console = None

        # Setup JSONL log file
        if self.enable_file:
            self._log_file = self.log_dir / f"ralph-{self._session_id}.jsonl"
            # Touch the file to ensure it exists
            self._log_file.touch(exist_ok=True)

        # Setup FIFO pipe for real-time streaming
        if self.enable_fifo:
            self._fifo_path = self.log_dir / "ralph-stream.fifo"
            self._setup_fifo()

    def _setup_fifo(self):
        """Create or recreate the FIFO pipe."""
        if self._fifo_path is None:
            return

        try:
            # Remove existing FIFO if present
            if self._fifo_path.exists():
                # Check if it's actually a FIFO
                if stat.S_ISFIFO(self._fifo_path.stat().st_mode):
                    self._fifo_path.unlink()
                else:
                    # It's a regular file, rename it
                    backup = self._fifo_path.with_suffix(".fifo.bak")
                    self._fifo_path.rename(backup)

            # Create new FIFO
            os.mkfifo(self._fifo_path)
        except (OSError, PermissionError) as e:
            # Disable FIFO if we can't create it
            self._fifo_path = None
            self.enable_fifo = False
            # Log to file if available
            if self.enable_file and self._log_file:
                self._write_to_file(StructuredLogEntry(
                    timestamp=datetime.now().isoformat(),
                    level="WARNING",
                    component="stream_logger",
                    message=f"Could not create FIFO pipe: {e}. FIFO disabled."
                ))

    def log(
        self,
        level: LogLevel,
        component: str,
        message: str,
        iteration: Optional[int] = None,
        context_tokens: Optional[int] = None,
        **metadata
    ):
        """
        Log a structured entry to all enabled outputs.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            component: Source component name
            message: Human-readable message
            iteration: Current iteration number
            context_tokens: Current context window token usage
            **metadata: Additional structured data
        """
        if self._closed:
            return

        if level.value < self.log_level.value:
            return

        entry = StructuredLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.name,
            component=component,
            message=message,
            iteration=iteration,
            context_tokens=context_tokens,
            metadata=metadata if metadata else None
        )

        with self._lock:
            # Console output (Rich formatted)
            if self.enable_console:
                self._write_to_console(entry)

            # File output (JSONL)
            if self.enable_file:
                self._write_to_file(entry)

            # FIFO pipe output (non-blocking)
            if self.enable_fifo:
                self._write_to_fifo(entry)

            # Custom callbacks
            for callback in self._callbacks:
                try:
                    callback(entry)
                except Exception:
                    pass  # Don't let callback errors break logging

    def _write_to_console(self, entry: StructuredLogEntry):
        """Write entry to console with Rich formatting."""
        if self._console:
            try:
                self._console.print(entry.to_rich(), highlight=False)
            except Exception:
                # Fallback to plain print
                print(entry.to_plain(), file=__import__("sys").stderr)
        else:
            print(entry.to_plain(), file=__import__("sys").stderr)

    def _write_to_file(self, entry: StructuredLogEntry):
        """Write entry to JSONL log file."""
        if self._log_file is None:
            return
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
                f.flush()
        except (OSError, IOError):
            pass  # Don't break on file write errors

    def _write_to_fifo(self, entry: StructuredLogEntry):
        """Write entry to FIFO pipe (non-blocking)."""
        if self._fifo_path is None or not self._fifo_path.exists():
            return
        try:
            # Non-blocking open and write
            fd = os.open(str(self._fifo_path), os.O_WRONLY | os.O_NONBLOCK)
            try:
                os.write(fd, (entry.to_json() + "\n").encode("utf-8"))
            finally:
                os.close(fd)
        except (OSError, BlockingIOError):
            # No reader on pipe or pipe full - skip silently
            pass

    def debug(self, component: str, message: str, **kwargs):
        """Log a DEBUG level message."""
        self.log(LogLevel.DEBUG, component, message, **kwargs)

    def info(self, component: str, message: str, **kwargs):
        """Log an INFO level message."""
        self.log(LogLevel.INFO, component, message, **kwargs)

    def warning(self, component: str, message: str, **kwargs):
        """Log a WARNING level message."""
        self.log(LogLevel.WARNING, component, message, **kwargs)

    def error(self, component: str, message: str, **kwargs):
        """Log an ERROR level message."""
        self.log(LogLevel.ERROR, component, message, **kwargs)

    def critical(self, component: str, message: str, **kwargs):
        """Log a CRITICAL level message."""
        self.log(LogLevel.CRITICAL, component, message, **kwargs)

    def add_callback(self, callback: Callable[[StructuredLogEntry], None]):
        """
        Register a callback for log entries.

        Args:
            callback: Function called with each StructuredLogEntry
        """
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[StructuredLogEntry], None]):
        """Remove a previously registered callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    @property
    def log_file_path(self) -> Optional[Path]:
        """Get the current JSONL log file path."""
        return self._log_file

    @property
    def fifo_path(self) -> Optional[Path]:
        """Get the FIFO pipe path if enabled."""
        return self._fifo_path

    def cleanup(self):
        """Clean up FIFO pipe and close resources."""
        with self._lock:
            self._closed = True
            if self._fifo_path and self._fifo_path.exists():
                try:
                    self._fifo_path.unlink()
                except (OSError, PermissionError):
                    pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
        return False

    def __del__(self):
        """Destructor to clean up FIFO pipe."""
        try:
            self.cleanup()
        except Exception:
            pass


# Convenience function for creating a pre-configured logger
def create_stream_logger(
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_fifo: bool = True,
    log_dir: Optional[str] = None
) -> StreamLogger:
    """
    Create a StreamLogger with string-based log level.

    Args:
        log_level: Log level as string (DEBUG, INFO, WARNING, ERROR)
        enable_console: Output to stderr
        enable_file: Output to JSONL file
        enable_fifo: Output to FIFO pipe
        log_dir: Optional log directory path

    Returns:
        Configured StreamLogger instance
    """
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "WARN": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
    }
    level = level_map.get(log_level.upper(), LogLevel.INFO)

    return StreamLogger(
        log_dir=Path(log_dir) if log_dir else None,
        log_level=level,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_fifo=enable_fifo
    )
