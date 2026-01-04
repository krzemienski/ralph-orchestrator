"""Tests for ContextManager prompt_text functionality."""


from ralph_orchestrator.context import ContextManager


class TestContextManagerPromptText:
    """Test ContextManager prompt_text functionality."""

    def test_prompt_text_overrides_file(self, tmp_path):
        """Test that prompt_text overrides prompt_file."""
        # Create a prompt file with different content
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("File prompt content")

        # Create ContextManager with both file and text
        cm = ContextManager(
            prompt_file=prompt_file,
            prompt_text="Direct prompt text",
            cache_dir=tmp_path / "cache"
        )

        # prompt_text should take priority
        assert cm.get_prompt() == "Direct prompt text"

    def test_prompt_text_without_file(self, tmp_path):
        """Test prompt_text when file doesn't exist."""
        prompt_file = tmp_path / "nonexistent.md"

        cm = ContextManager(
            prompt_file=prompt_file,
            prompt_text="Direct prompt",
            cache_dir=tmp_path / "cache"
        )

        assert cm.get_prompt() == "Direct prompt"

    def test_falls_back_to_file_when_no_text(self, tmp_path):
        """Test fallback to prompt_file when prompt_text is None."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("File content here")

        cm = ContextManager(
            prompt_file=prompt_file,
            prompt_text=None,
            cache_dir=tmp_path / "cache"
        )

        assert cm.get_prompt() == "File content here"

    def test_empty_prompt_when_no_text_no_file(self, tmp_path):
        """Test empty prompt when neither text nor file exists."""
        prompt_file = tmp_path / "nonexistent.md"

        cm = ContextManager(
            prompt_file=prompt_file,
            prompt_text=None,
            cache_dir=tmp_path / "cache"
        )

        assert cm.get_prompt() == ""

    def test_prompt_text_with_headers(self, tmp_path):
        """Test prompt_text with markdown headers extracts stable prefix."""
        prompt_text = """# Task
Build a REST API

## Requirements
- Fast
- Secure
"""
        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text=prompt_text,
            cache_dir=tmp_path / "cache"
        )

        assert "# Task" in cm.get_prompt()
        assert cm.stable_prefix is not None
        assert "# Task" in cm.stable_prefix

    def test_prompt_text_multiline(self, tmp_path):
        """Test multiline prompt_text is preserved."""
        prompt_text = """Line 1
Line 2
Line 3"""

        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text=prompt_text,
            cache_dir=tmp_path / "cache"
        )

        result = cm.get_prompt()
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_prompt_text_optimization(self, tmp_path):
        """Test that large prompt_text gets optimized."""
        # Create a very large prompt
        large_prompt = "# Header\n\n" + "Content " * 2000

        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text=large_prompt,
            max_context_size=1000,
            cache_dir=tmp_path / "cache"
        )

        result = cm.get_prompt()
        # Should be optimized (shorter than original)
        assert len(result) <= cm.max_context_size + 100

    def test_prompt_text_with_dynamic_context(self, tmp_path):
        """Test prompt_text with dynamic context updates."""
        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text="Base prompt",
            cache_dir=tmp_path / "cache"
        )

        # Update context
        cm.update_context("Success: Task completed")

        result = cm.get_prompt()
        assert "Base prompt" in result

    def test_context_reset_with_prompt_text(self, tmp_path):
        """Test context reset preserves prompt_text."""
        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text="Original prompt",
            cache_dir=tmp_path / "cache"
        )

        cm.update_context("Some context")
        cm.add_error_feedback("Some error")
        cm.reset()

        # prompt_text should still work after reset
        assert "Original prompt" in cm.get_prompt()


class TestContextManagerCacheResilience:
    """Test ContextManager resilience when cache directory is deleted mid-run."""

    def test_survives_cache_deletion_during_optimization(self, tmp_path):
        """Test that cache deletion during run doesn't crash optimization.

        Reproduces bug where agent deleted .agent/ directory and subsequent
        iterations failed with FileNotFoundError when writing to cache.
        """
        import shutil

        # Create a large prompt that triggers optimization
        large_prompt = "# Header\n\n" + "Content " * 2000
        cache_dir = tmp_path / "cache"

        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text=large_prompt,
            max_context_size=1000,
            cache_dir=cache_dir
        )

        # Verify cache dir exists
        assert cache_dir.exists()

        # First call should succeed and create cache file
        result1 = cm.get_prompt()
        assert len(result1) <= 1100  # Optimized

        # Delete the cache directory (simulating agent cleanup)
        shutil.rmtree(cache_dir)
        assert not cache_dir.exists()

        # This should NOT crash - it should recreate cache
        result2 = cm.get_prompt()
        assert len(result2) <= 1100  # Still optimized
        assert cache_dir.exists()  # Cache dir recreated

    def test_survives_agent_directory_deletion(self, tmp_path):
        """Test full .agent/ deletion scenario."""
        import shutil

        agent_dir = tmp_path / ".agent"
        cache_dir = agent_dir / "cache"

        large_prompt = "# Task\n\n" + "Details " * 2000

        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text=large_prompt,
            max_context_size=1000,
            cache_dir=cache_dir
        )

        # First call succeeds
        cm.get_prompt()
        assert cache_dir.exists()

        # Agent deletes entire .agent/ directory
        shutil.rmtree(agent_dir)
        assert not agent_dir.exists()

        # Should recover gracefully
        result = cm.get_prompt()
        assert result  # Not empty
        assert cache_dir.exists()  # Recreated


class TestContextManagerBackwardsCompatibility:
    """Test backwards compatibility without prompt_text."""

    def test_default_file_based_behavior(self, tmp_path):
        """Test default behavior with just prompt_file."""
        prompt_file = tmp_path / "PROMPT.md"
        prompt_file.write_text("File-based prompt")

        # Old-style initialization without prompt_text
        cm = ContextManager(
            prompt_file=prompt_file,
            cache_dir=tmp_path / "cache"
        )

        assert cm.get_prompt() == "File-based prompt"

    def test_stats_with_prompt_text(self, tmp_path):
        """Test stats work with prompt_text."""
        cm = ContextManager(
            prompt_file=tmp_path / "ignored.md",
            prompt_text="Test prompt",
            cache_dir=tmp_path / "cache"
        )

        stats = cm.get_stats()
        assert "stable_prefix_size" in stats
        assert "dynamic_context_items" in stats
