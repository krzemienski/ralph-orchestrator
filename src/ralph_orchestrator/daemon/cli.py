# ABOUTME: CLI functions for daemon control commands
# ABOUTME: Provides start/stop/status/logs operations for ralph daemon

import os
import signal
from pathlib import Path
from typing import Dict, Any, Optional, Iterator


def get_default_paths() -> Dict[str, Path]:
    """Get default paths for daemon files."""
    ralph_dir = Path.home() / ".ralph"
    return {
        "pid_file": ralph_dir / "daemon.pid",
        "log_file": ralph_dir / "logs" / "daemon.log",
    }


def daemon_status(pid_file: Optional[Path] = None) -> Dict[str, Any]:
    """Check daemon status.

    Args:
        pid_file: Path to PID file (default: ~/.ralph/daemon.pid)

    Returns:
        Dict with keys:
        - running: bool - whether daemon is running
        - pid: int - process ID if running
        - message: str - human-readable status message
    """
    if pid_file is None:
        pid_file = get_default_paths()["pid_file"]

    if not pid_file.exists():
        return {
            "running": False,
            "message": "Daemon is not running (no PID file)",
        }

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        # Invalid PID file, clean up
        try:
            pid_file.unlink()
        except OSError:
            pass
        return {
            "running": False,
            "message": "Daemon is not running (invalid PID file)",
        }

    # Check if process is actually running
    try:
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        return {
            "running": True,
            "pid": pid,
            "message": f"Daemon is running (PID: {pid})",
        }
    except ProcessLookupError:
        # Process not running, clean up stale PID file
        try:
            pid_file.unlink()
        except OSError:
            pass
        return {
            "running": False,
            "message": "Daemon is not running (stale PID file cleaned up)",
        }
    except PermissionError:
        # Can't check - assume running
        return {
            "running": True,
            "pid": pid,
            "message": f"Daemon appears to be running (PID: {pid}, permission denied)",
        }


def daemon_start(
    pid_file: Optional[Path] = None,
    log_file: Optional[Path] = None,
    prompt_file: Optional[str] = None,
    test_mode: bool = False,
) -> Dict[str, Any]:
    """Start the daemon.

    Args:
        pid_file: Path to PID file (default: ~/.ralph/daemon.pid)
        log_file: Path to log file (default: ~/.ralph/logs/daemon.log)
        prompt_file: Path to prompt file to run
        test_mode: If True, don't actually fork (for testing)

    Returns:
        Dict with keys:
        - success: bool - whether start succeeded
        - pid: int - daemon PID if started
        - message: str - human-readable result message
    """
    defaults = get_default_paths()
    if pid_file is None:
        pid_file = defaults["pid_file"]
    if log_file is None:
        log_file = defaults["log_file"]

    # Ensure directories exist
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if already running
    status = daemon_status(pid_file)
    if status["running"]:
        return {
            "success": False,
            "pid": status.get("pid"),
            "message": f"Daemon is already running (PID: {status.get('pid')})",
        }

    if test_mode:
        # In test mode, just write current PID and return success
        pid_file.write_text(str(os.getpid()))
        return {
            "success": True,
            "pid": os.getpid(),
            "message": f"Daemon started in test mode (PID: {os.getpid()})",
        }

    # Import DaemonManager for actual forking
    from .manager import DaemonManager

    manager = DaemonManager(pid_file=pid_file)

    # Define what the daemon will run
    def run_orchestrator():
        """Run the orchestrator in daemon mode."""
        import logging
        from ralph_orchestrator.orchestrator import RalphOrchestrator
        from ralph_orchestrator.main import RalphConfig

        # Set up logging to file
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        if prompt_file:
            config = RalphConfig(prompt_file=prompt_file)
            orchestrator = RalphOrchestrator(config)
            orchestrator.run()

    # Start the daemon
    manager.start(run_orchestrator)

    # If we reach here, we're the parent and daemon was forked
    # Wait briefly for PID file to be created
    import time
    for _ in range(10):
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                return {
                    "success": True,
                    "pid": pid,
                    "message": f"Daemon started (PID: {pid})",
                }
            except (ValueError, OSError):
                pass
        time.sleep(0.1)

    return {
        "success": True,
        "message": "Daemon starting (PID file not yet created)",
    }


def daemon_stop(pid_file: Optional[Path] = None) -> Dict[str, Any]:
    """Stop the daemon.

    Args:
        pid_file: Path to PID file (default: ~/.ralph/daemon.pid)

    Returns:
        Dict with keys:
        - success: bool - whether stop succeeded
        - message: str - human-readable result message
    """
    if pid_file is None:
        pid_file = get_default_paths()["pid_file"]

    # Check if running
    status = daemon_status(pid_file)
    if not status["running"]:
        return {
            "success": False,
            "message": "Daemon is not running",
        }

    pid = status["pid"]

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)

        # Wait for process to terminate
        import time
        for _ in range(50):  # Wait up to 5 seconds
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except ProcessLookupError:
                break

        # Clean up PID file
        try:
            pid_file.unlink()
        except OSError:
            pass

        return {
            "success": True,
            "message": f"Daemon stopped (was PID: {pid})",
        }

    except ProcessLookupError:
        # Already dead
        try:
            pid_file.unlink()
        except OSError:
            pass
        return {
            "success": True,
            "message": "Daemon was not running (cleaned up stale PID)",
        }

    except PermissionError:
        return {
            "success": False,
            "message": f"Permission denied stopping daemon (PID: {pid})",
        }


def daemon_logs(
    log_file: Optional[Path] = None,
    tail: Optional[int] = None,
    follow: bool = False,
) -> Dict[str, Any]:
    """Get daemon logs.

    Args:
        log_file: Path to log file (default: ~/.ralph/logs/daemon.log)
        tail: Number of lines from end to return (None = all)
        follow: If True, continuously watch for new lines

    Returns:
        Dict with keys:
        - success: bool - whether operation succeeded
        - content: str - log content (if not follow mode)
        - follow_mode: bool - True if in follow mode
        - message: str - human-readable result message
    """
    if log_file is None:
        log_file = get_default_paths()["log_file"]

    if not log_file.exists():
        return {
            "success": False,
            "content": "",
            "message": "No log file found",
        }

    if follow:
        # Follow mode - return indicator that caller should handle streaming
        return {
            "success": True,
            "follow_mode": True,
            "log_file": str(log_file),
            "message": "Follow mode - stream from log file",
        }

    try:
        content = log_file.read_text()

        if tail is not None and tail > 0:
            lines = content.splitlines()
            content = "\n".join(lines[-tail:])
            if lines[-1:] and lines[-1]:
                content += "\n"

        return {
            "success": True,
            "content": content,
            "message": f"Retrieved logs from {log_file}",
        }

    except OSError as e:
        return {
            "success": False,
            "content": "",
            "message": f"Error reading log file: {e}",
        }
