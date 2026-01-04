# ABOUTME: Log forwarding with rotation and streaming for daemon processes
# ABOUTME: Enables persistent logging and real-time log streaming via IPC

import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, List, Optional


class LogForwarder:
    """Log forwarder for daemon processes.

    Provides:
    - Persistent logging to ~/.ralph/logs/
    - Log rotation with configurable size and backup limits
    - Real-time streaming via callbacks
    - Tail and follow functionality for CLI
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB default
        max_backups: int = 5
    ):
        """Initialize the log forwarder.

        Args:
            log_dir: Directory for log files. Defaults to ~/.ralph/logs
            max_size_bytes: Max log file size before rotation
            max_backups: Max number of backup files to keep
        """
        self.log_dir = log_dir or (Path.home() / ".ralph" / "logs")
        self.max_size_bytes = max_size_bytes
        self.max_backups = max_backups
        self._callbacks: List[Callable[[str, str], None]] = []
        self._lock = threading.Lock()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def write(self, message: str, instance_id: str = "daemon") -> None:
        """Write a log message for an instance.

        Args:
            message: Log message to write
            instance_id: Instance identifier for the log file
        """
        log_file = self.log_dir / f"{instance_id}.log"
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}\n"

        with self._lock:
            # Check if rotation needed before writing
            if log_file.exists() and log_file.stat().st_size >= self.max_size_bytes:
                self._rotate(instance_id)

            # Append to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)

        # Notify all registered callbacks
        for callback in self._callbacks:
            try:
                callback(message, instance_id)
            except Exception:
                pass  # Don't let callback errors affect logging

    def _rotate(self, instance_id: str) -> None:
        """Rotate log file for an instance.

        Args:
            instance_id: Instance identifier
        """
        log_file = self.log_dir / f"{instance_id}.log"
        if not log_file.exists():
            return

        # Shift existing backups
        for i in range(self.max_backups - 1, 0, -1):
            old_backup = self.log_dir / f"{instance_id}.log.{i}"
            new_backup = self.log_dir / f"{instance_id}.log.{i + 1}"
            if old_backup.exists():
                if new_backup.exists():
                    new_backup.unlink()
                old_backup.rename(new_backup)

        # Move current log to .1
        backup_path = self.log_dir / f"{instance_id}.log.1"
        if backup_path.exists():
            backup_path.unlink()
        log_file.rename(backup_path)

        # Clean up old backups beyond max_backups
        for backup in self.log_dir.glob(f"{instance_id}.log.*"):
            try:
                suffix = backup.suffix
                if suffix.startswith("."):
                    backup_num = int(suffix[1:])
                    if backup_num > self.max_backups:
                        backup.unlink()
            except (ValueError, OSError):
                pass

    def register_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for log streaming.

        Callback receives (message, instance_id) for each log write.

        Args:
            callback: Function to call with new log messages
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, str], None]) -> None:
        """Unregister a streaming callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def read_tail(self, instance_id: str = "daemon", n: int = 10) -> List[str]:
        """Read the last N lines from a log file.

        Args:
            instance_id: Instance identifier
            n: Number of lines to return

        Returns:
            List of last N log lines
        """
        log_file = self.log_dir / f"{instance_id}.log"
        if not log_file.exists():
            return []

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                return [line.rstrip("\n") for line in lines[-n:]]
        except OSError:
            return []

    def read_follow(
        self,
        instance_id: str = "daemon",
        stop_event: Optional[threading.Event] = None
    ) -> Iterator[str]:
        """Follow a log file, yielding new lines as they're written.

        Args:
            instance_id: Instance identifier
            stop_event: Event to signal when to stop following

        Yields:
            New log lines as they're written
        """
        log_file = self.log_dir / f"{instance_id}.log"

        # Wait for file to exist
        while not log_file.exists():
            if stop_event and stop_event.is_set():
                return
            time.sleep(0.1)

        with open(log_file, "r", encoding="utf-8") as f:
            # Seek to end of file
            f.seek(0, os.SEEK_END)

            while True:
                if stop_event and stop_event.is_set():
                    break

                line = f.readline()
                if line:
                    yield line.rstrip("\n")
                else:
                    # No new data, wait a bit
                    time.sleep(0.1)
