# ABOUTME: Tool call tracking with timing, streaming, and call stack management
# ABOUTME: Provides START/END events for tool calls with duration metrics

"""
Tool call tracking with timing and streaming.

This module provides infrastructure for tracking tool calls with:
- START/END event emission via StreamLogger
- Call duration timing in milliseconds
- Nested call tracking via parent_call_id
- Tool call summary statistics
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .stream_logger import StreamLogger


@dataclass
class ToolCallEvent:
    """
    Represents a single tool call with timing and metadata.

    Attributes:
        tool_name: Name of the tool being called
        arguments: Arguments passed to the tool
        start_time: When the tool call started
        end_time: When the tool call completed (None if still running)
        result: Tool execution result (truncated for logging)
        success: Whether the call succeeded
        error: Error message if call failed
        parent_call_id: ID of parent call for nested tracking
        call_id: Unique identifier for this call
    """
    tool_name: str
    arguments: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    parent_call_id: Optional[str] = None
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def to_log_entry(self) -> dict:
        """Convert to structured log entry format."""
        return {
            "type": "tool_call",
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments_preview": str(self.arguments)[:200],
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "result_preview": str(self.result)[:200] if self.result else None,
            "parent_call_id": self.parent_call_id
        }


class ToolCallTracker:
    """
    Track and stream tool calls with timing.

    This tracker maintains:
    - A call stack for nested tool calls
    - History of all tool calls for summary statistics
    - Integration with StreamLogger for real-time event emission

    Example:
        tracker = ToolCallTracker(stream_logger=logger)
        event = tracker.start_call("Read", {"file_path": "/foo/bar.py"})
        # ... tool executes ...
        tracker.end_call(event, result="file content", success=True)

        # Get summary
        summary = tracker.get_summary()
        print(f"Total calls: {summary['total_calls']}")
    """

    def __init__(self, stream_logger: Optional["StreamLogger"] = None):
        """
        Initialize ToolCallTracker.

        Args:
            stream_logger: Optional StreamLogger for emitting events
        """
        self.stream_logger = stream_logger
        self._call_stack: List[ToolCallEvent] = []
        self._all_calls: List[ToolCallEvent] = []

    def start_call(self, tool_name: str, arguments: dict) -> ToolCallEvent:
        """
        Record start of a tool call.

        Args:
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool

        Returns:
            ToolCallEvent representing this call (pass to end_call)
        """
        parent_id = self._call_stack[-1].call_id if self._call_stack else None
        event = ToolCallEvent(
            tool_name=tool_name,
            arguments=arguments,
            start_time=datetime.now(),
            parent_call_id=parent_id
        )
        self._call_stack.append(event)
        self._all_calls.append(event)

        if self.stream_logger:
            self.stream_logger.info(
                "ToolCall",
                f"START {tool_name}",
                tool_name=tool_name,
                call_id=event.call_id,
                args_preview=str(arguments)[:100]
            )
        return event

    def end_call(
        self,
        event: ToolCallEvent,
        result: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Record end of a tool call.

        Args:
            event: The ToolCallEvent returned from start_call
            result: Result string from the tool (truncated in logs)
            success: Whether the call succeeded
            error: Error message if call failed
        """
        event.end_time = datetime.now()
        event.result = result
        event.success = success
        event.error = error

        # Pop from call stack if it's the current call
        if self._call_stack and self._call_stack[-1].call_id == event.call_id:
            self._call_stack.pop()

        if self.stream_logger:
            status = "SUCCESS" if success else "FAILED"
            duration_str = f"{event.duration_ms:.0f}ms" if event.duration_ms else "?"
            self.stream_logger.info(
                "ToolCall",
                f"END {event.tool_name} [{status}] ({duration_str})",
                tool_name=event.tool_name,
                call_id=event.call_id,
                duration_ms=event.duration_ms,
                success=success,
                error=error
            )

    def get_current_call(self) -> Optional[ToolCallEvent]:
        """Get the currently executing tool call (top of stack)."""
        return self._call_stack[-1] if self._call_stack else None

    def get_call_depth(self) -> int:
        """Get current nesting depth of tool calls."""
        return len(self._call_stack)

    def get_all_calls(self) -> List[ToolCallEvent]:
        """Get all recorded tool calls."""
        return self._all_calls.copy()

    def get_summary(self) -> dict:
        """
        Get summary statistics of all tool calls.

        Returns:
            Dictionary with total_calls, successful, failed,
            total_duration_ms, and by_tool breakdown
        """
        return {
            "total_calls": len(self._all_calls),
            "successful": sum(1 for c in self._all_calls if c.success),
            "failed": sum(1 for c in self._all_calls if not c.success),
            "total_duration_ms": sum(c.duration_ms or 0 for c in self._all_calls),
            "by_tool": self._group_by_tool()
        }

    def _group_by_tool(self) -> dict:
        """Group call statistics by tool name."""
        groups: Dict[str, Dict[str, Any]] = {}
        for call in self._all_calls:
            if call.tool_name not in groups:
                groups[call.tool_name] = {"count": 0, "total_ms": 0, "failed": 0}
            groups[call.tool_name]["count"] += 1
            groups[call.tool_name]["total_ms"] += call.duration_ms or 0
            if not call.success:
                groups[call.tool_name]["failed"] += 1
        return groups

    def reset(self):
        """Clear all tracking data."""
        self._call_stack.clear()
        self._all_calls.clear()
