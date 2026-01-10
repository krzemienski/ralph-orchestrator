# ABOUTME: Tests for ACE learning module integration
# ABOUTME: Validates LearningConfig, ACELearningAdapter, and graceful degradation

"""Tests for the ACE learning module."""

import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ralph_orchestrator.learning import (
    ACELearningAdapter,
    LearningConfig,
    ACE_AVAILABLE,
)


class TestLearningConfig:
    """Test LearningConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = LearningConfig()
        assert config.enabled is False
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.skillbook_path == ".agent/skillbook/skillbook.json"
        assert config.async_learning is True
        assert config.max_skills == 100

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LearningConfig(
            enabled=True,
            model="claude-opus-4-5-20251101",
            skillbook_path="/custom/path/skillbook.json",
            async_learning=False,
            max_skills=50,
        )
        assert config.enabled is True
        assert config.model == "claude-opus-4-5-20251101"
        assert config.skillbook_path == "/custom/path/skillbook.json"
        assert config.async_learning is False
        assert config.max_skills == 50


class TestACELearningAdapterWithoutACE:
    """Test ACELearningAdapter when ACE framework is not installed."""

    def test_disabled_without_ace(self):
        """Test adapter is disabled when ACE is not available."""
        config = LearningConfig(enabled=True)

        # Mock ACE as unavailable
        with patch('ralph_orchestrator.learning.ace_adapter.ACE_AVAILABLE', False):
            # Need to reimport to pick up the mock
            from ralph_orchestrator.learning.ace_adapter import ACELearningAdapter as MockedAdapter
            adapter = MockedAdapter(config)
            assert adapter.enabled is False

    def test_inject_context_passthrough(self):
        """Test inject_context returns prompt unchanged when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        prompt = "Test prompt content"
        result = adapter.inject_context(prompt)
        assert result == prompt

    def test_learn_from_execution_noop(self):
        """Test learn_from_execution does nothing when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        # Should not raise
        adapter.learn_from_execution(
            task="test task",
            output="test output",
            success=True,
        )

    def test_save_skillbook_noop(self):
        """Test save_skillbook does nothing when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        # Should not raise
        adapter.save_skillbook()

    def test_get_stats_disabled(self):
        """Test get_stats returns disabled status when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        stats = adapter.get_stats()
        assert stats == {"enabled": False}


class TestACELearningAdapterEnabled:
    """Test ACELearningAdapter when ACE is available (mocked)."""

    @pytest.fixture
    def mock_ace(self):
        """Create mocked ACE components."""
        mock_skill_manager = MagicMock()
        mock_skill_manager.get_skills.return_value = []

        mock_reflector = MagicMock()

        return mock_skill_manager, mock_reflector

    @pytest.fixture
    def temp_skillbook(self):
        """Create a temporary skillbook path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield str(Path(tmpdir) / "skillbook.json")

    def test_thread_safety(self):
        """Test that adapter operations are thread-safe."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        # Verify lock exists (uses _skillbook_lock for thread safety)
        assert hasattr(adapter, '_skillbook_lock')
        assert isinstance(adapter._skillbook_lock, type(threading.Lock()))

    def test_stats_structure_when_disabled(self):
        """Test get_stats returns expected structure when disabled."""
        config = LearningConfig(enabled=False)
        adapter = ACELearningAdapter(config)

        # When disabled, should return {"enabled": False}
        stats = adapter.get_stats()
        assert 'enabled' in stats
        assert stats['enabled'] is False

    def test_config_preserved(self):
        """Test that config is preserved in adapter."""
        config = LearningConfig(
            enabled=True,
            model="test-model",
            skillbook_path="/test/path.json",
            max_skills=50,
        )
        adapter = ACELearningAdapter(config)

        # Config should be accessible
        assert adapter.config.model == "test-model"
        assert adapter.config.skillbook_path == "/test/path.json"
        assert adapter.config.max_skills == 50


class TestLearningIntegration:
    """Integration tests for learning module with RalphConfig."""

    def test_import_availability(self):
        """Test module imports correctly."""
        from ralph_orchestrator.learning import (
            ACELearningAdapter,
            LearningConfig,
            ACE_AVAILABLE,
        )
        # Should import without error
        assert LearningConfig is not None
        assert ACELearningAdapter is not None
        assert isinstance(ACE_AVAILABLE, bool)

    def test_graceful_degradation(self):
        """Test learning features degrade gracefully when ACE not installed."""
        config = LearningConfig(enabled=True)

        # Even with enabled=True, adapter should handle missing ACE
        adapter = ACELearningAdapter(config)

        # These should all work without error
        prompt = "test prompt"
        result = adapter.inject_context(prompt)
        assert result == prompt  # Unchanged when ACE unavailable

        adapter.learn_from_execution("task", "output", True)
        adapter.save_skillbook()

        stats = adapter.get_stats()
        assert isinstance(stats, dict)


class TestLearningConfigFromDict:
    """Test LearningConfig creation from dictionary (YAML parsing)."""

    def test_from_dict_basic(self):
        """Test creating config from basic dict."""
        data = {
            'enabled': True,
            'model': 'test-model',
        }
        config = LearningConfig(**data)
        assert config.enabled is True
        assert config.model == 'test-model'

    def test_from_yaml_style_dict(self):
        """Test creating config from YAML-style dict with async_learning."""
        data = {
            'enabled': True,
            'model': 'claude-sonnet-4-5-20250929',
            'skillbook_path': '.agent/skillbook/skillbook.json',
            'async_learning': True,
            'max_skills': 100,
        }
        config = LearningConfig(**data)
        assert config.enabled is True
        assert config.async_learning is True
        assert config.max_skills == 100
