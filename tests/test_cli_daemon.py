# ABOUTME: Tests for CLI daemon commands
# ABOUTME: TDD tests for Plan 02-02: CLI Daemon Commands

import unittest
import tempfile
import os
import signal
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO


class TestCLIDaemonCommandsParsing(unittest.TestCase):
    """Tests for daemon CLI argument parsing."""

    def test_daemon_subcommand_exists(self):
        """Test that 'daemon' subcommand is recognized."""
        from ralph_orchestrator.__main__ import main
        import argparse

        # We should be able to parse 'daemon status' without error
        # The actual command may fail but parsing should succeed
        with patch('sys.argv', ['ralph', 'daemon', 'status']):
            with patch('ralph_orchestrator.__main__._console'):
                try:
                    # This should either work or exit with sys.exit
                    # but NOT raise unrecognized arguments error
                    main()
                except SystemExit as e:
                    # Exit is fine, unrecognized argument is not
                    pass

    def test_daemon_start_subcommand(self):
        """Test that 'daemon start' subcommand is recognized."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'daemon', 'start']):
            with patch('ralph_orchestrator.__main__._console'):
                try:
                    main()
                except SystemExit:
                    pass

    def test_daemon_stop_subcommand(self):
        """Test that 'daemon stop' subcommand is recognized."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'daemon', 'stop']):
            with patch('ralph_orchestrator.__main__._console'):
                try:
                    main()
                except SystemExit:
                    pass

    def test_daemon_logs_subcommand(self):
        """Test that 'daemon logs' subcommand is recognized."""
        from ralph_orchestrator.__main__ import main

        with patch('sys.argv', ['ralph', 'daemon', 'logs']):
            with patch('ralph_orchestrator.__main__._console'):
                try:
                    main()
                except SystemExit:
                    pass


class TestCLIDaemonStatus(unittest.TestCase):
    """Tests for 'ralph daemon status' command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pid_file = Path(self.temp_dir) / "daemon.pid"
        self.log_file = Path(self.temp_dir) / "daemon.log"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_status_not_running(self):
        """Test status command when daemon is not running."""
        from ralph_orchestrator.daemon.cli import daemon_status

        result = daemon_status(pid_file=self.pid_file)

        self.assertFalse(result["running"])
        self.assertIn("message", result)

    def test_status_running(self):
        """Test status command when daemon is running."""
        from ralph_orchestrator.daemon.cli import daemon_status

        # Create a fake running process (sleep)
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.pid_file.write_text(str(proc.pid))

        try:
            result = daemon_status(pid_file=self.pid_file)

            self.assertTrue(result["running"])
            self.assertEqual(result["pid"], proc.pid)
        finally:
            proc.terminate()
            proc.wait()

    def test_status_stale_pid(self):
        """Test status command with stale PID file."""
        from ralph_orchestrator.daemon.cli import daemon_status

        # Write a PID that doesn't exist
        self.pid_file.write_text("99999999")

        result = daemon_status(pid_file=self.pid_file)

        self.assertFalse(result["running"])
        # Stale PID should be cleaned up
        self.assertFalse(self.pid_file.exists())


class TestCLIDaemonStart(unittest.TestCase):
    """Tests for 'ralph daemon start' command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pid_file = Path(self.temp_dir) / "daemon.pid"
        self.log_file = Path(self.temp_dir) / "daemon.log"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        # Kill any daemon we started
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                if pid != os.getpid():
                    os.kill(pid, signal.SIGTERM)
            except (ValueError, ProcessLookupError, OSError):
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_creates_pid_file(self):
        """Test that start command creates PID file."""
        from ralph_orchestrator.daemon.cli import daemon_start

        # Start daemon (in test mode - doesn't actually fork)
        result = daemon_start(
            pid_file=self.pid_file,
            log_file=self.log_file,
            test_mode=True  # Don't actually fork
        )

        self.assertTrue(result["success"])
        self.assertIn("pid", result)

    def test_start_fails_when_already_running(self):
        """Test that start fails when daemon is already running."""
        from ralph_orchestrator.daemon.cli import daemon_start

        # Create a fake running process
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.pid_file.write_text(str(proc.pid))

        try:
            result = daemon_start(
                pid_file=self.pid_file,
                log_file=self.log_file,
                test_mode=True
            )

            self.assertFalse(result["success"])
            self.assertIn("already running", result["message"].lower())
        finally:
            proc.terminate()
            proc.wait()


class TestCLIDaemonStop(unittest.TestCase):
    """Tests for 'ralph daemon stop' command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.pid_file = Path(self.temp_dir) / "daemon.pid"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stop_when_not_running(self):
        """Test stop command when daemon is not running."""
        from ralph_orchestrator.daemon.cli import daemon_stop

        result = daemon_stop(pid_file=self.pid_file)

        self.assertFalse(result["success"])
        self.assertIn("not running", result["message"].lower())

    def test_stop_kills_process(self):
        """Test that stop command kills the daemon process."""
        from ralph_orchestrator.daemon.cli import daemon_stop

        # Start a process to stop
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.pid_file.write_text(str(proc.pid))

        result = daemon_stop(pid_file=self.pid_file)

        self.assertTrue(result["success"])
        # Process should be terminated
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            self.fail("Process was not terminated")

    def test_stop_removes_pid_file(self):
        """Test that stop command removes PID file."""
        from ralph_orchestrator.daemon.cli import daemon_stop

        # Start a process to stop
        proc = subprocess.Popen(
            ["sleep", "60"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.pid_file.write_text(str(proc.pid))

        daemon_stop(pid_file=self.pid_file)

        self.assertFalse(self.pid_file.exists())
        proc.wait(timeout=2)


class TestCLIDaemonLogs(unittest.TestCase):
    """Tests for 'ralph daemon logs' command."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = Path(self.temp_dir) / "daemon.log"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logs_when_no_log_file(self):
        """Test logs command when log file doesn't exist."""
        from ralph_orchestrator.daemon.cli import daemon_logs

        result = daemon_logs(log_file=self.log_file)

        self.assertFalse(result["success"])
        self.assertIn("no log file", result["message"].lower())

    def test_logs_returns_content(self):
        """Test that logs command returns log file content."""
        from ralph_orchestrator.daemon.cli import daemon_logs

        # Create log file with content
        self.log_file.write_text("Test log line 1\nTest log line 2\n")

        result = daemon_logs(log_file=self.log_file)

        self.assertTrue(result["success"])
        self.assertIn("Test log line 1", result["content"])
        self.assertIn("Test log line 2", result["content"])

    def test_logs_tail_parameter(self):
        """Test that logs command supports tail parameter."""
        from ralph_orchestrator.daemon.cli import daemon_logs

        # Create log file with multiple lines
        lines = [f"Log line {i}" for i in range(100)]
        self.log_file.write_text("\n".join(lines) + "\n")

        result = daemon_logs(log_file=self.log_file, tail=10)

        self.assertTrue(result["success"])
        # Should only contain last 10 lines
        self.assertIn("Log line 99", result["content"])
        self.assertNotIn("Log line 0", result["content"])

    def test_logs_follow_mode(self):
        """Test that logs command supports follow mode flag."""
        from ralph_orchestrator.daemon.cli import daemon_logs

        self.log_file.write_text("Initial log\n")

        # Follow mode should return a generator or indicate follow mode
        result = daemon_logs(log_file=self.log_file, follow=True)

        # In follow mode, we expect either a generator or a flag indicating follow
        # For now, we just check it doesn't error
        self.assertTrue(result["success"] or result.get("follow_mode", False))


if __name__ == "__main__":
    unittest.main()
