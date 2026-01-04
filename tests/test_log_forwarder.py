# ABOUTME: Tests for log forwarding functionality
# ABOUTME: TDD tests for Plan 02-04: Log Forwarding

import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading


class TestLogForwarderBasics(unittest.TestCase):
    """Tests for LogForwarder basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import_log_forwarder(self):
        """Test that LogForwarder can be imported."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        self.assertIsNotNone(LogForwarder)

    def test_init_creates_log_directory(self):
        """Test that LogForwarder creates log directory if missing."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)
        self.assertTrue(self.log_dir.exists())

    def test_init_default_log_directory(self):
        """Test that LogForwarder defaults to ~/.ralph/logs."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder()
        expected = Path.home() / ".ralph" / "logs"
        self.assertEqual(forwarder.log_dir, expected)


class TestLogWriting(unittest.TestCase):
    """Tests for writing logs to files."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_creates_log_file(self):
        """Test that writing creates a log file."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)
        forwarder.write("test message", instance_id="test123")

        log_file = self.log_dir / "test123.log"
        self.assertTrue(log_file.exists())

    def test_write_appends_to_log_file(self):
        """Test that writing appends to existing log file."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)
        forwarder.write("message 1", instance_id="test123")
        forwarder.write("message 2", instance_id="test123")

        log_file = self.log_dir / "test123.log"
        content = log_file.read_text()
        self.assertIn("message 1", content)
        self.assertIn("message 2", content)

    def test_write_includes_timestamp(self):
        """Test that written logs include timestamp."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)
        forwarder.write("test message", instance_id="test123")

        log_file = self.log_dir / "test123.log"
        content = log_file.read_text()
        # Should contain ISO-like timestamp
        self.assertRegex(content, r"\d{4}-\d{2}-\d{2}")

    def test_write_default_instance_id(self):
        """Test that write uses 'daemon' as default instance_id."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)
        forwarder.write("test message")

        log_file = self.log_dir / "daemon.log"
        self.assertTrue(log_file.exists())


class TestLogRotation(unittest.TestCase):
    """Tests for log rotation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_rotate_creates_backup_file(self):
        """Test that rotation creates a backup file."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        # Use very small size to ensure rotation happens
        forwarder = LogForwarder(log_dir=self.log_dir, max_size_bytes=50)

        # Write multiple times to ensure file exceeds limit
        for i in range(5):
            forwarder.write("A" * 30, instance_id="test123")

        # Check for rotated file
        rotated_files = list(self.log_dir.glob("test123.log.*"))
        self.assertGreater(len(rotated_files), 0)

    def test_rotate_keeps_max_backups(self):
        """Test that rotation respects max_backups limit."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(
            log_dir=self.log_dir,
            max_size_bytes=50,
            max_backups=2
        )

        # Write enough to trigger multiple rotations
        for i in range(5):
            forwarder.write("X" * 60, instance_id="test123")

        # Should have at most 2 backup files
        rotated_files = list(self.log_dir.glob("test123.log.*"))
        self.assertLessEqual(len(rotated_files), 2)


class TestLogStreaming(unittest.TestCase):
    """Tests for real-time log streaming."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_callback(self):
        """Test that callbacks can be registered for log streaming."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        received_logs = []
        def callback(message, instance_id):
            received_logs.append((message, instance_id))

        forwarder.register_callback(callback)
        forwarder.write("test message", instance_id="test123")

        self.assertEqual(len(received_logs), 1)
        self.assertEqual(received_logs[0][0], "test message")
        self.assertEqual(received_logs[0][1], "test123")

    def test_unregister_callback(self):
        """Test that callbacks can be unregistered."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        received_logs = []
        def callback(message, instance_id):
            received_logs.append((message, instance_id))

        forwarder.register_callback(callback)
        forwarder.unregister_callback(callback)
        forwarder.write("test message", instance_id="test123")

        self.assertEqual(len(received_logs), 0)

    def test_multiple_callbacks(self):
        """Test that multiple callbacks can receive logs."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        received_1 = []
        received_2 = []

        forwarder.register_callback(lambda msg, id: received_1.append(msg))
        forwarder.register_callback(lambda msg, id: received_2.append(msg))
        forwarder.write("test message", instance_id="test123")

        self.assertEqual(len(received_1), 1)
        self.assertEqual(len(received_2), 1)


class TestLogReading(unittest.TestCase):
    """Tests for reading log files."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_tail_returns_last_lines(self):
        """Test that read_tail returns last N lines."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        for i in range(10):
            forwarder.write(f"line {i}", instance_id="test123")

        lines = forwarder.read_tail(instance_id="test123", n=3)
        self.assertEqual(len(lines), 3)
        self.assertIn("line 9", lines[-1])
        self.assertIn("line 8", lines[-2])
        self.assertIn("line 7", lines[-3])

    def test_read_tail_handles_nonexistent_file(self):
        """Test that read_tail returns empty list for nonexistent file."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        lines = forwarder.read_tail(instance_id="nonexistent", n=10)
        self.assertEqual(lines, [])

    def test_read_follow_yields_new_lines(self):
        """Test that read_follow yields new lines as they're written."""
        from ralph_orchestrator.daemon.log_forwarder import LogForwarder
        forwarder = LogForwarder(log_dir=self.log_dir)

        # Pre-create log file
        forwarder.write("initial line", instance_id="test123")

        received_lines = []
        stop_event = threading.Event()

        def follow_thread():
            for line in forwarder.read_follow(instance_id="test123", stop_event=stop_event):
                received_lines.append(line)
                if len(received_lines) >= 2:
                    stop_event.set()
                    break

        thread = threading.Thread(target=follow_thread)
        thread.start()

        # Give thread time to start
        time.sleep(0.1)

        # Write new lines
        forwarder.write("new line 1", instance_id="test123")
        forwarder.write("new line 2", instance_id="test123")

        # Wait for thread
        thread.join(timeout=2)
        stop_event.set()

        self.assertGreaterEqual(len(received_lines), 1)


if __name__ == "__main__":
    unittest.main()
