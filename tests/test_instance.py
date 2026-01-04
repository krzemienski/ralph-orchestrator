# ABOUTME: Tests for instance management system
# ABOUTME: Verifies UUID generation, persistence, and cleanup

import pytest
import tempfile
import os
from pathlib import Path
from ralph_orchestrator.instance import InstanceManager, InstanceInfo


class TestInstanceInfo:
    """Test InstanceInfo dataclass."""

    def test_instance_info_defaults(self):
        """InstanceInfo has sensible defaults."""
        info = InstanceInfo(
            id="test1234",
            pid=12345,
            prompt_file="test.md",
            state_dir="/tmp/test",
        )
        assert info.id == "test1234"
        assert info.pid == 12345
        assert info.status == "running"
        assert info.web_port is None
        assert info.started_at > 0

    def test_instance_info_with_all_fields(self):
        """InstanceInfo accepts all fields."""
        info = InstanceInfo(
            id="test1234",
            pid=12345,
            prompt_file="test.md",
            state_dir="/tmp/test",
            web_port=8080,
            started_at=1234567890.0,
            status="completed",
        )
        assert info.web_port == 8080
        assert info.started_at == 1234567890.0
        assert info.status == "completed"


class TestInstanceManager:
    """Test InstanceManager class."""

    def test_init_creates_directories(self):
        """InstanceManager creates base directories on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "ralph"
            mgr = InstanceManager(base)
            assert mgr.instances_dir.exists()

    def test_create_instance_unique_id(self):
        """Each created instance gets a unique ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            i1 = mgr.create_instance("prompt1.md")
            i2 = mgr.create_instance("prompt2.md")
            assert i1.id != i2.id
            assert len(i1.id) == 8
            assert len(i2.id) == 8

    def test_create_instance_creates_state_dir(self):
        """Creating instance creates its state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            assert Path(info.state_dir).exists()
            assert f"state-{info.id}" in info.state_dir

    def test_create_instance_saves_to_disk(self):
        """Instance info is persisted to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            json_file = mgr.instances_dir / f"{info.id}.json"
            assert json_file.exists()

    def test_get_instance_returns_saved(self):
        """Can retrieve a saved instance by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            created = mgr.create_instance("prompt.md")
            retrieved = mgr.get_instance(created.id)
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.prompt_file == created.prompt_file

    def test_get_instance_returns_none_for_missing(self):
        """Returns None for non-existent instance ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            result = mgr.get_instance("nonexistent")
            assert result is None

    def test_list_instances_returns_all(self):
        """List returns all created instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            mgr.create_instance("p1.md")
            mgr.create_instance("p2.md")
            mgr.create_instance("p3.md")
            instances = mgr.list_instances()
            assert len(instances) == 3

    def test_list_instances_empty_when_none(self):
        """List returns empty when no instances exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            instances = mgr.list_instances()
            assert len(instances) == 0

    def test_cleanup_instance_removes_file(self):
        """Cleanup removes the instance JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            json_file = mgr.instances_dir / f"{info.id}.json"
            assert json_file.exists()
            mgr.cleanup_instance(info.id)
            assert not json_file.exists()

    def test_cleanup_nonexistent_instance_no_error(self):
        """Cleaning up non-existent instance doesn't raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            mgr.cleanup_instance("nonexistent")  # Should not raise

    def test_update_status(self):
        """Can update instance status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            mgr.update_status(info.id, "completed")
            updated = mgr.get_instance(info.id)
            assert updated.status == "completed"

    def test_update_port(self):
        """Can update instance web port."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            assert info.web_port is None
            mgr.update_port(info.id, 8080)
            updated = mgr.get_instance(info.id)
            assert updated.web_port == 8080

    def test_list_running_filters_dead_processes(self):
        """List running only returns instances with active PIDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            # Create instance with current PID (should be running)
            running_info = mgr.create_instance("running.md")

            # Create instance with fake dead PID
            dead_info = InstanceInfo(
                id="deadbeef",
                pid=999999,  # Very unlikely to be running
                prompt_file="dead.md",
                state_dir=str(Path(tmpdir) / "state-deadbeef"),
            )
            mgr._save_instance(dead_info)

            running = mgr.list_running()
            running_ids = [i.id for i in running]

            # Current process should be in running list
            assert running_info.id in running_ids
            # Dead process should have been cleaned up
            assert "deadbeef" not in running_ids

    def test_is_pid_running_current_process(self):
        """Current process PID should be detected as running."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            assert mgr._is_pid_running(os.getpid()) is True

    def test_is_pid_running_invalid_pid(self):
        """Invalid PID should be detected as not running."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            assert mgr._is_pid_running(999999999) is False


class TestDynamicPortAllocation:
    """Test dynamic port allocation for parallel instances."""

    def test_find_available_port_returns_port_in_range(self):
        """find_available_port returns a port within the configured range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            port = mgr.find_available_port()
            assert 8080 <= port <= 8180

    def test_find_available_port_returns_unused_port(self):
        """find_available_port returns a port that can be bound."""
        import socket
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            port = mgr.find_available_port()
            # Verify we can actually bind to this port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(("127.0.0.1", port))
                sock.close()
            except OSError:
                pytest.fail(f"Port {port} should be available but cannot be bound")

    def test_find_available_port_skips_ports_used_by_instances(self):
        """find_available_port skips ports already assigned to instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            # Create instance with port 8080
            info = mgr.create_instance("prompt.md")
            mgr.update_port(info.id, 8080)
            # Next port should skip 8080
            port = mgr.find_available_port()
            assert port != 8080

    def test_find_available_port_with_multiple_instances(self):
        """find_available_port returns unique ports for each call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            ports = set()
            for i in range(5):
                port = mgr.find_available_port()
                ports.add(port)
                # Simulate instance using the port
                info = mgr.create_instance(f"prompt{i}.md")
                mgr.update_port(info.id, port)
            # All ports should be unique
            assert len(ports) == 5

    def test_allocate_port_assigns_and_persists(self):
        """allocate_port assigns a port to instance and persists it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            info = mgr.create_instance("prompt.md")
            port = mgr.allocate_port(info.id)
            assert 8080 <= port <= 8180
            # Verify persistence
            updated = mgr.get_instance(info.id)
            assert updated.web_port == port

    def test_get_used_ports_returns_all_instance_ports(self):
        """get_used_ports returns ports from all running instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = InstanceManager(Path(tmpdir))
            # Create instances with ports
            i1 = mgr.create_instance("p1.md")
            mgr.update_port(i1.id, 8080)
            i2 = mgr.create_instance("p2.md")
            mgr.update_port(i2.id, 8085)
            used = mgr.get_used_ports()
            assert 8080 in used
            assert 8085 in used
