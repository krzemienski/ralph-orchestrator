# ABOUTME: Tests for TUI widget components
# ABOUTME: Tests widget instantiation, state management, and data updates

import pytest
from unittest.mock import Mock, patch
from collections import deque

from ralph_orchestrator.tui.widgets import (
    ProgressPanel,
    OutputViewer,
    TaskSidebar,
    MetricsPanel,
)
from ralph_orchestrator.tui.widgets.tasks import Task, TaskItem
from ralph_orchestrator.tui.widgets.metrics import MetricWidget


class TestProgressPanel:
    """Test progress panel widget."""

    def test_progress_panel_creates(self):
        """ProgressPanel widget can be instantiated."""
        panel = ProgressPanel()
        assert panel is not None

    def test_progress_panel_has_reactive_properties(self):
        """ProgressPanel has expected reactive properties defined on class."""
        # Check reactive descriptors exist on the class (not instance)
        # Accessing them on instance triggers Textual runtime checks
        assert "current_iteration" in dir(ProgressPanel)
        assert "max_iterations" in dir(ProgressPanel)
        assert "current_task" in dir(ProgressPanel)
        assert "status" in dir(ProgressPanel)
        assert "is_paused" in dir(ProgressPanel)
        assert "elapsed_seconds" in dir(ProgressPanel)
        assert "cost" in dir(ProgressPanel)
        assert "max_cost" in dir(ProgressPanel)
        assert "connection_status" in dir(ProgressPanel)

    def test_progress_panel_has_methods(self):
        """ProgressPanel has expected public methods."""
        panel = ProgressPanel()

        assert hasattr(panel, "update_iteration")
        assert hasattr(panel, "set_paused")
        assert hasattr(panel, "set_connection_status")
        assert hasattr(panel, "update_cost")
        assert hasattr(panel, "mark_complete")


class TestOutputViewer:
    """Test output viewer widget."""

    def test_output_viewer_creates(self):
        """OutputViewer widget can be instantiated."""
        viewer = OutputViewer()
        assert viewer is not None

    def test_output_viewer_has_auto_scroll(self):
        """OutputViewer has auto_scroll reactive property."""
        viewer = OutputViewer()
        assert hasattr(viewer, "auto_scroll")
        # Default should be True
        assert viewer.auto_scroll is True

    def test_output_viewer_has_methods(self):
        """OutputViewer has expected public methods."""
        viewer = OutputViewer()

        assert hasattr(viewer, "append_agent_output")
        assert hasattr(viewer, "append_tool_call")
        assert hasattr(viewer, "append_iteration_marker")
        assert hasattr(viewer, "append_error")
        assert hasattr(viewer, "append_validation_gate")
        assert hasattr(viewer, "toggle_auto_scroll")
        assert hasattr(viewer, "clear_output")


class TestTaskSidebar:
    """Test task sidebar widget."""

    def test_task_sidebar_creates(self):
        """TaskSidebar widget can be instantiated."""
        sidebar = TaskSidebar()
        assert sidebar is not None

    def test_task_sidebar_has_reactive_properties(self):
        """TaskSidebar has expected reactive properties."""
        sidebar = TaskSidebar()
        assert hasattr(sidebar, "is_collapsed")

    def test_task_sidebar_has_methods(self):
        """TaskSidebar has expected public methods."""
        sidebar = TaskSidebar()

        assert hasattr(sidebar, "update_tasks")
        assert hasattr(sidebar, "toggle_collapse")
        assert hasattr(sidebar, "get_task_summary")

    def test_task_sidebar_initial_state(self):
        """TaskSidebar has correct initial state."""
        sidebar = TaskSidebar()

        # Internal lists should be empty
        assert sidebar._pending == []
        assert sidebar._current is None
        assert sidebar._completed == []

    def test_task_sidebar_summary_empty(self):
        """TaskSidebar returns correct summary when empty."""
        sidebar = TaskSidebar()
        summary = sidebar.get_task_summary()

        assert summary["pending"] == 0
        assert summary["running"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0


class TestTask:
    """Test Task dataclass."""

    def test_task_creation(self):
        """Task dataclass can be created."""
        task = Task(id="1", name="Test Task", status="pending")
        assert task.id == "1"
        assert task.name == "Test Task"
        assert task.status == "pending"
        assert task.duration is None
        assert task.error is None

    def test_task_with_all_fields(self):
        """Task can be created with all fields."""
        task = Task(
            id="2",
            name="Completed Task",
            status="completed",
            duration=5.5,
            error=None,
        )
        assert task.duration == 5.5

    def test_task_with_error(self):
        """Task can be created with error."""
        task = Task(
            id="3",
            name="Failed Task",
            status="failed",
            error="Something went wrong",
        )
        assert task.error == "Something went wrong"


class TestTaskItem:
    """Test TaskItem widget."""

    def test_task_item_creates(self):
        """TaskItem can be created with a Task."""
        task = Task(id="1", name="Test", status="pending")
        item = TaskItem(task)
        assert item is not None
        assert item._task_data is task


class TestMetricsPanel:
    """Test metrics panel widget."""

    def test_metrics_panel_creates(self):
        """MetricsPanel widget can be instantiated."""
        panel = MetricsPanel()
        assert panel is not None

    def test_metrics_panel_has_methods(self):
        """MetricsPanel has expected public methods."""
        panel = MetricsPanel()

        assert hasattr(panel, "update_metrics")
        assert hasattr(panel, "get_current_metrics")


class TestMetricWidget:
    """Test individual metric widget."""

    def test_metric_widget_creates(self):
        """MetricWidget can be instantiated."""
        widget = MetricWidget(label="Test", icon="🔧", unit="%")
        assert widget is not None

    def test_metric_widget_stores_config(self):
        """MetricWidget stores configuration."""
        widget = MetricWidget(
            label="CPU",
            icon="⚙",
            unit="%",
            max_value=100.0,
            format_spec=".0f",
        )
        assert widget.label == "CPU"
        assert widget.icon == "⚙"
        assert widget.unit == "%"
        assert widget.max_value == 100.0
        assert widget.format_spec == ".0f"

    def test_metric_widget_has_history(self):
        """MetricWidget has history deque."""
        widget = MetricWidget(label="Test")
        assert hasattr(widget, "_history")
        assert isinstance(widget._history, deque)
        assert widget._history.maxlen == 60

    def test_metric_widget_has_methods(self):
        """MetricWidget has expected methods."""
        widget = MetricWidget(label="Test")

        assert hasattr(widget, "update_value")


class TestWidgetCSS:
    """Test widgets have CSS defined."""

    def test_progress_panel_has_css(self):
        """ProgressPanel has DEFAULT_CSS."""
        assert hasattr(ProgressPanel, "DEFAULT_CSS")
        assert len(ProgressPanel.DEFAULT_CSS) > 0

    def test_output_viewer_has_css(self):
        """OutputViewer has DEFAULT_CSS."""
        assert hasattr(OutputViewer, "DEFAULT_CSS")
        assert len(OutputViewer.DEFAULT_CSS) > 0

    def test_task_sidebar_has_css(self):
        """TaskSidebar has DEFAULT_CSS."""
        assert hasattr(TaskSidebar, "DEFAULT_CSS")
        assert len(TaskSidebar.DEFAULT_CSS) > 0

    def test_metrics_panel_has_css(self):
        """MetricsPanel has DEFAULT_CSS."""
        assert hasattr(MetricsPanel, "DEFAULT_CSS")
        assert len(MetricsPanel.DEFAULT_CSS) > 0

    def test_metric_widget_has_css(self):
        """MetricWidget has DEFAULT_CSS."""
        assert hasattr(MetricWidget, "DEFAULT_CSS")
        assert len(MetricWidget.DEFAULT_CSS) > 0


class TestValidationPrompt:
    """Test validation prompt widget."""

    def test_validation_prompt_import(self):
        """ValidationPrompt can be imported."""
        from ralph_orchestrator.tui.widgets import ValidationPrompt

        assert ValidationPrompt is not None
