# ABOUTME: Manages unique instance identification for parallel ralph runs
# ABOUTME: Enables multiple orchestrators to run without conflicts

import uuid
import json
import os
import socket
import time
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Set

# Port range for dynamic allocation (101 ports available)
PORT_RANGE_START = 8080
PORT_RANGE_END = 8180


@dataclass
class InstanceInfo:
    """Information about a ralph instance."""

    id: str
    pid: int
    prompt_file: str
    state_dir: str
    web_port: Optional[int] = None
    started_at: float = field(default_factory=time.time)
    status: str = "running"


class InstanceManager:
    """Manage ralph instance lifecycle and identification."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize instance manager.

        Args:
            base_dir: Base directory for ralph data. Defaults to ~/.ralph
        """
        self.base_dir = base_dir or Path.home() / ".ralph"
        self.instances_dir = self.base_dir / "instances"
        self.instances_dir.mkdir(parents=True, exist_ok=True)

    def create_instance(self, prompt_file: str) -> InstanceInfo:
        """Create a new instance with unique ID.

        Args:
            prompt_file: Path to the prompt file being executed

        Returns:
            InstanceInfo with unique ID and state directory
        """
        instance_id = str(uuid.uuid4())[:8]
        state_dir = self.base_dir / f"state-{instance_id}"
        state_dir.mkdir(parents=True, exist_ok=True)

        info = InstanceInfo(
            id=instance_id,
            pid=os.getpid(),
            prompt_file=prompt_file,
            state_dir=str(state_dir),
        )
        self._save_instance(info)
        return info

    def _save_instance(self, info: InstanceInfo) -> None:
        """Persist instance info to disk.

        Args:
            info: Instance information to save
        """
        info_file = self.instances_dir / f"{info.id}.json"
        info_file.write_text(json.dumps(asdict(info), indent=2))

    def get_instance(self, instance_id: str) -> Optional[InstanceInfo]:
        """Get instance by ID.

        Args:
            instance_id: The 8-character instance ID

        Returns:
            InstanceInfo if found, None otherwise
        """
        info_file = self.instances_dir / f"{instance_id}.json"
        if not info_file.exists():
            return None
        data = json.loads(info_file.read_text())
        return InstanceInfo(**data)

    def list_instances(self) -> List[InstanceInfo]:
        """List all known instances.

        Returns:
            List of all instance info objects
        """
        instances = []
        for f in self.instances_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                instances.append(InstanceInfo(**data))
            except (json.JSONDecodeError, TypeError):
                continue
        return instances

    def list_running(self) -> List[InstanceInfo]:
        """List only running instances (PID still active).

        Returns:
            List of instances with active processes
        """
        running = []
        for inst in self.list_instances():
            if self._is_pid_running(inst.pid):
                running.append(inst)
            else:
                self.cleanup_instance(inst.id)
        return running

    def _is_pid_running(self, pid: int) -> bool:
        """Check if a PID is still running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running
        """
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def cleanup_instance(self, instance_id: str) -> None:
        """Remove instance info file.

        Args:
            instance_id: ID of instance to clean up
        """
        info_file = self.instances_dir / f"{instance_id}.json"
        if info_file.exists():
            info_file.unlink()

    def update_status(self, instance_id: str, status: str) -> None:
        """Update instance status.

        Args:
            instance_id: ID of instance to update
            status: New status string
        """
        info = self.get_instance(instance_id)
        if info:
            info.status = status
            self._save_instance(info)

    def update_port(self, instance_id: str, port: int) -> None:
        """Update instance web port.

        Args:
            instance_id: ID of instance to update
            port: Port number assigned to this instance
        """
        info = self.get_instance(instance_id)
        if info:
            info.web_port = port
            self._save_instance(info)

    def get_used_ports(self) -> Set[int]:
        """Get all ports currently assigned to instances.

        Returns:
            Set of port numbers in use by existing instances
        """
        ports = set()
        for instance in self.list_instances():
            if instance.web_port is not None:
                ports.add(instance.web_port)
        return ports

    def find_available_port(
        self, start: int = PORT_RANGE_START, end: int = PORT_RANGE_END
    ) -> int:
        """Find an available port within the configured range.

        Checks both instance assignments and actual port availability.

        Args:
            start: Start of port range (default: 8080)
            end: End of port range (default: 8180)

        Returns:
            An available port number

        Raises:
            RuntimeError: If no ports are available in the range
        """
        used_ports = self.get_used_ports()

        for port in range(start, end + 1):
            if port in used_ports:
                continue
            if self._is_port_available(port):
                return port

        raise RuntimeError(f"No available ports in range {start}-{end}")

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding.

        Args:
            port: Port number to check

        Returns:
            True if port can be bound, False otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            return True
        except OSError:
            return False

    def allocate_port(self, instance_id: str) -> int:
        """Allocate an available port to an instance.

        Finds an available port, assigns it to the instance, and persists.

        Args:
            instance_id: ID of instance to allocate port to

        Returns:
            The allocated port number

        Raises:
            RuntimeError: If no ports are available
        """
        port = self.find_available_port()
        self.update_port(instance_id, port)
        return port
