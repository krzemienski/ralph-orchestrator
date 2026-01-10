# ABOUTME: Context window usage tracking and visualization
# ABOUTME: Uses tiktoken for accurate token counting with fallback estimation

"""
Context window usage tracking and visualization.
Uses tiktoken for accurate token counting.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, TYPE_CHECKING
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

if TYPE_CHECKING:
    from ralph_orchestrator.logging.stream_logger import StreamLogger


class MeasurePoint(Enum):
    """Measurement points in the orchestration lifecycle."""
    ITERATION_START = "iteration_start"
    AFTER_PROMPT_INJECT = "after_prompt_inject"
    AFTER_SKILLBOOK_INJECT = "after_skillbook_inject"
    AFTER_TOOL_CALL = "after_tool_call"
    AFTER_RESPONSE = "after_response"
    ITERATION_END = "iteration_end"


@dataclass
class ContextMeasurement:
    """A single context measurement at a point in time.

    Attributes:
        timestamp: ISO format timestamp of measurement
        iteration: Current iteration number
        measure_point: Type of measurement (from MeasurePoint enum)
        tokens: Token count at this point
        chars: Character count at this point
        component: Description of what was added/measured
        delta_tokens: Change from previous measurement
        cumulative_tokens: Running total in this iteration
        context_limit: Maximum context window size
        percentage_used: Percentage of context limit used
    """
    timestamp: str
    iteration: int
    measure_point: str
    tokens: int
    chars: int
    component: str  # What was added
    delta_tokens: int  # Change from previous measurement
    cumulative_tokens: int  # Total so far in iteration
    context_limit: int
    percentage_used: float

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class IterationContextSummary:
    """Summary of context usage for a single iteration."""
    iteration: int
    start_tokens: int
    end_tokens: int
    peak_tokens: int
    prompt_tokens: int
    response_tokens: int
    tool_tokens: int
    skillbook_tokens: int


class ContextTracker:
    """Track context window usage throughout orchestration.

    Provides token counting, visualization, and persistence for
    understanding how context is consumed during orchestration runs.

    Example:
        tracker = ContextTracker(adapter_type="claude")
        tracker.measure(MeasurePoint.ITERATION_START, prompt, "initial_prompt", iteration=1)
        tracker.measure(MeasurePoint.AFTER_TOOL_CALL, result, "tool_result")
        print(tracker.get_timeline_ascii())
        tracker.save_timeline()
    """

    # Context limits by adapter
    CONTEXT_LIMITS = {
        "claude": 200_000,
        "gemini": 32_000,
        "qchat": 8_000,
        "kiro": 8_000,
        "default": 100_000
    }

    def __init__(
        self,
        adapter_type: str = "claude",
        output_dir: Path = Path(".agent/metrics"),
        stream_logger: Optional["StreamLogger"] = None
    ):
        """Initialize ContextTracker.

        Args:
            adapter_type: Type of adapter (affects context limit)
            output_dir: Directory for timeline JSON output
            stream_logger: Optional StreamLogger for real-time streaming
        """
        self.adapter_type = adapter_type
        self.context_limit = self.CONTEXT_LIMITS.get(adapter_type, self.CONTEXT_LIMITS["default"])
        self.output_dir = Path(output_dir)
        self.stream_logger = stream_logger
        self._measurements: List[ContextMeasurement] = []
        self._current_iteration = 0
        self._iteration_baseline = 0

        # Initialize tiktoken encoder
        if TIKTOKEN_AVAILABLE:
            self._encoder = tiktoken.encoding_for_model("gpt-4")  # Compatible with Claude
        else:
            self._encoder = None

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses tiktoken if available, otherwise falls back to
        character-based estimation (~4 chars per token).

        Args:
            text: Text to count tokens in

        Returns:
            Estimated token count
        """
        if self._encoder:
            return len(self._encoder.encode(text))
        else:
            # Fallback: ~4 chars per token
            return len(text) // 4

    def measure(
        self,
        point: MeasurePoint,
        content: str,
        component: str,
        iteration: Optional[int] = None
    ) -> ContextMeasurement:
        """Record a context measurement.

        Args:
            point: Type of measurement point
            content: Content to measure (full context at this point)
            component: Description of what was added
            iteration: Override current iteration number

        Returns:
            ContextMeasurement recorded
        """
        if iteration is not None:
            self._current_iteration = iteration

        tokens = self.count_tokens(content)
        chars = len(content)

        # Calculate delta from previous measurement in same iteration
        prev_in_iteration = [m for m in self._measurements if m.iteration == self._current_iteration]
        if prev_in_iteration:
            delta = tokens - prev_in_iteration[-1].tokens
            cumulative = prev_in_iteration[-1].cumulative_tokens + max(0, delta)
        else:
            delta = tokens
            cumulative = tokens
            self._iteration_baseline = tokens

        measurement = ContextMeasurement(
            timestamp=datetime.now().isoformat(),
            iteration=self._current_iteration,
            measure_point=point.value,
            tokens=tokens,
            chars=chars,
            component=component,
            delta_tokens=delta,
            cumulative_tokens=cumulative,
            context_limit=self.context_limit,
            percentage_used=(cumulative / self.context_limit) * 100
        )

        self._measurements.append(measurement)

        # Stream to logger
        if self.stream_logger:
            emoji = self._get_usage_emoji(measurement.percentage_used)
            self.stream_logger.info(
                "Context",
                f"{emoji} {point.value}: {tokens:,} tokens ({measurement.percentage_used:.1f}% of {self.context_limit:,})",
                iteration=self._current_iteration,
                context_tokens=tokens,
                percentage=measurement.percentage_used,
                component=component
            )

        return measurement

    def _get_usage_emoji(self, percentage: float) -> str:
        """Get emoji indicator for usage level.

        Args:
            percentage: Usage percentage (0-100)

        Returns:
            Colored emoji indicating severity
        """
        if percentage < 50:
            return "🟢"
        elif percentage < 80:
            return "🟡"
        elif percentage < 95:
            return "🟠"
        else:
            return "🔴"

    def get_timeline_ascii(self, width: int = 60) -> str:
        """Generate ASCII visualization of context usage over time.

        Args:
            width: Total width of the visualization

        Returns:
            Multi-line ASCII string showing usage bars per measurement
        """
        if not self._measurements:
            return "No measurements recorded"

        lines = []
        lines.append(f"Context Usage Timeline (limit: {self.context_limit:,} tokens)")
        lines.append("=" * width)

        # Group by iteration
        iterations: Dict[int, List[ContextMeasurement]] = {}
        for m in self._measurements:
            if m.iteration not in iterations:
                iterations[m.iteration] = []
            iterations[m.iteration].append(m)

        for iter_num, measurements in sorted(iterations.items()):
            lines.append(f"\nIteration {iter_num}:")
            lines.append("-" * width)

            for m in measurements:
                # Create bar
                bar_width = width - 40
                filled = int((m.percentage_used / 100) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)
                emoji = self._get_usage_emoji(m.percentage_used)

                point_name = m.measure_point.replace("_", " ").title()[:15].ljust(15)
                lines.append(f"  {point_name} |{bar}| {m.percentage_used:5.1f}% {emoji}")

        return "\n".join(lines)

    def get_summary(self) -> Dict:
        """Get summary statistics of all measurements.

        Returns:
            Dictionary with aggregate statistics
        """
        if not self._measurements:
            return {"error": "No measurements"}

        return {
            "total_measurements": len(self._measurements),
            "iterations_tracked": len(set(m.iteration for m in self._measurements)),
            "peak_usage_percent": max(m.percentage_used for m in self._measurements),
            "peak_tokens": max(m.tokens for m in self._measurements),
            "context_limit": self.context_limit,
            "adapter": self.adapter_type
        }

    def save_timeline(self, filename: str = None) -> Path:
        """Save timeline data to JSON file.

        Args:
            filename: Optional filename (default: auto-generated with timestamp)

        Returns:
            Path to created JSON file
        """
        if filename is None:
            filename = f"context-timeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

        filepath = self.output_dir / filename
        data = {
            "metadata": {
                "adapter": self.adapter_type,
                "context_limit": self.context_limit,
                "generated_at": datetime.now().isoformat()
            },
            "summary": self.get_summary(),
            "measurements": [m.to_dict() for m in self._measurements]
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def print_timeline(self):
        """Print ASCII timeline to console."""
        print(self.get_timeline_ascii())

    def reset(self):
        """Clear all measurements."""
        self._measurements.clear()
        self._current_iteration = 0
        self._iteration_baseline = 0

    def get_measurements(self) -> List[ContextMeasurement]:
        """Get all recorded measurements."""
        return self._measurements.copy()
