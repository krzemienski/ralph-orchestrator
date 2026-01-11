"""Tests for the prompt transformation module.

Following TDD: Each test is written BEFORE the implementation.
"""
import pytest
from dataclasses import dataclass


class TestPromptTransformer:
    """Tests for PromptTransformer class."""

    def test_transformer_exists(self):
        """RED: PromptTransformer class should exist."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        assert transformer is not None

    def test_transform_returns_result(self):
        """RED: transform() should return a TransformResult."""
        from ralph_orchestrator.transform import PromptTransformer, TransformResult

        transformer = PromptTransformer()
        result = transformer.transform("Simple task: create a hello world script")

        assert isinstance(result, TransformResult)

    def test_transform_result_has_original(self):
        """RED: TransformResult should contain original prompt."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        original = "Simple task: create a hello world script"
        result = transformer.transform(original)

        assert result.original == original

    def test_transform_result_has_transformed(self):
        """RED: TransformResult should contain transformed prompt."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        result = transformer.transform("Simple task: create a hello world script")

        assert result.transformed is not None
        assert isinstance(result.transformed, str)

    def test_transform_adds_completion_marker_if_missing(self):
        """RED: Transform should add completion section if missing."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        original = """# Task
Create a hello world script in Python.

## Requirements
- Print "Hello, World!"
- Make it executable
"""
        result = transformer.transform(original)

        # Should contain the TASK_COMPLETE marker
        assert "TASK_COMPLETE" in result.transformed
        # Should contain completion section
        assert "## Completion" in result.transformed or "## Completion Status" in result.transformed

    def test_transform_preserves_existing_completion_marker(self):
        """RED: Transform should NOT duplicate completion marker if present."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        original = """# Task
Create a hello world script.

## Requirements
- Print "Hello, World!"

## Completion Status
- [ ] TASK_COMPLETE
"""
        result = transformer.transform(original)

        # Should have exactly one TASK_COMPLETE
        count = result.transformed.count("TASK_COMPLETE")
        assert count == 1


class TestTransformResult:
    """Tests for TransformResult dataclass."""

    def test_transform_result_fields(self):
        """RED: TransformResult should have required fields."""
        from ralph_orchestrator.transform import TransformResult

        result = TransformResult(
            original="test",
            transformed="test transformed",
            analysis={},
            validation={"valid": True},
            changes=[]
        )

        assert result.original == "test"
        assert result.transformed == "test transformed"
        assert result.analysis == {}
        assert result.validation == {"valid": True}
        assert result.changes == []


class TestTransformContext:
    """Tests for TransformContext runtime context."""

    def test_context_with_working_directory(self):
        """RED: TransformContext should accept working_directory."""
        from ralph_orchestrator.transform import TransformContext

        context = TransformContext(working_directory="/tmp/test")
        assert context.working_directory == "/tmp/test"

    def test_context_with_iteration(self):
        """RED: TransformContext should accept iteration number."""
        from ralph_orchestrator.transform import TransformContext

        context = TransformContext(iteration=3)
        assert context.iteration == 3

    def test_transform_uses_context_for_path_resolution(self):
        """RED: Transform should inject working directory from context."""
        from ralph_orchestrator.transform import PromptTransformer, TransformContext

        transformer = PromptTransformer()
        context = TransformContext(working_directory="/Users/test/project")
        original = "Create a file in the current directory"

        result = transformer.transform(original, context=context)

        # Should contain the working directory
        assert "/Users/test/project" in result.transformed


class TestCompletionAnalyzer:
    """Tests for completion detection analysis."""

    def test_analyzer_detects_missing_completion(self):
        """RED: Should detect when completion marker is missing."""
        from ralph_orchestrator.transform.analyzers import CompletionAnalyzer

        analyzer = CompletionAnalyzer()
        prompt = "# Task\nCreate hello world"

        analysis = analyzer.analyze(prompt)

        assert analysis["has_completion_marker"] is False
        assert analysis["has_completion_section"] is False

    def test_analyzer_detects_existing_completion(self):
        """RED: Should detect when completion marker exists."""
        from ralph_orchestrator.transform.analyzers import CompletionAnalyzer

        analyzer = CompletionAnalyzer()
        prompt = """# Task
Create hello world

## Completion Status
- [ ] TASK_COMPLETE
"""
        analysis = analyzer.analyze(prompt)

        assert analysis["has_completion_marker"] is True
        assert analysis["has_completion_section"] is True


class TestCompletionEnricher:
    """Tests for completion section enrichment."""

    def test_enricher_adds_completion_section(self):
        """RED: Should add completion section to prompt."""
        from ralph_orchestrator.transform.enrichers import CompletionEnricher

        enricher = CompletionEnricher()
        prompt = "# Task\nCreate hello world"
        analysis = {"has_completion_marker": False, "has_completion_section": False}

        enriched = enricher.enrich(prompt, analysis)

        assert "## Completion Status" in enriched
        assert "- [ ] TASK_COMPLETE" in enriched

    def test_enricher_skips_if_marker_exists(self):
        """RED: Should not modify prompt if completion marker exists."""
        from ralph_orchestrator.transform.enrichers import CompletionEnricher

        enricher = CompletionEnricher()
        prompt = """# Task
Create hello world

## Completion Status
- [ ] TASK_COMPLETE
"""
        analysis = {"has_completion_marker": True, "has_completion_section": True}

        enriched = enricher.enrich(prompt, analysis)

        # Should be unchanged (or minimal changes)
        assert enriched.count("TASK_COMPLETE") == 1


class TestPathResolutionEnricher:
    """Tests for path resolution header injection."""

    def test_enricher_adds_runtime_context(self):
        """RED: Should add runtime context header with working directory."""
        from ralph_orchestrator.transform.enrichers import PathResolutionEnricher
        from ralph_orchestrator.transform import TransformContext

        enricher = PathResolutionEnricher()
        prompt = "# Task\nCreate hello world"
        context = TransformContext(working_directory="/Users/test/project")

        enriched = enricher.enrich(prompt, {}, context)

        assert "Working Directory:" in enriched
        assert "/Users/test/project" in enriched

    def test_enricher_skips_without_context(self):
        """RED: Should not add header if no context provided."""
        from ralph_orchestrator.transform.enrichers import PathResolutionEnricher

        enricher = PathResolutionEnricher()
        prompt = "# Task\nCreate hello world"

        enriched = enricher.enrich(prompt, {}, None)

        # Should be unchanged
        assert enriched == prompt


class TestScratchpadEnricher:
    """Tests for scratchpad management enrichment."""

    def test_enricher_adds_hint_when_scratchpad_in_context(self):
        """Should add scratchpad hint when scratchpad path in context."""
        from ralph_orchestrator.transform.enrichers import ScratchpadEnricher
        from ralph_orchestrator.transform import TransformContext

        enricher = ScratchpadEnricher()
        prompt = "# Task\nCreate hello world"
        context = TransformContext(scratchpad_path=".agent/scratchpad.md")

        enriched = enricher.enrich(prompt, {}, context)

        assert "SCRATCHPAD" in enriched
        assert "cleared" in enriched.lower() or "namespace" in enriched.lower()

    def test_enricher_skips_without_scratchpad(self):
        """Should not modify if no scratchpad in context."""
        from ralph_orchestrator.transform.enrichers import ScratchpadEnricher
        from ralph_orchestrator.transform import TransformContext

        enricher = ScratchpadEnricher()
        prompt = "# Task\nCreate hello world"
        context = TransformContext(working_directory="/tmp")

        enriched = enricher.enrich(prompt, {}, context)

        assert enriched == prompt


class TestEdgeCases:
    """Edge case tests for transformation."""

    def test_empty_prompt_handled(self):
        """Should handle empty prompt gracefully."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        result = transformer.transform("")

        assert result.original == ""
        assert "TASK_COMPLETE" in result.transformed

    def test_multiline_prompt_preserved(self):
        """Should preserve multiline structure."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        original = """# Task Title

## Description
This is a multi-paragraph description
that spans several lines.

## Requirements
- First requirement
- Second requirement
"""
        result = transformer.transform(original)

        # Original structure should be preserved
        assert "# Task Title" in result.transformed
        assert "## Description" in result.transformed
        assert "multi-paragraph" in result.transformed
        assert "- First requirement" in result.transformed

    def test_loop_complete_detected_as_marker(self):
        """Should detect LOOP_COMPLETE as completion marker."""
        from ralph_orchestrator.transform.analyzers import CompletionAnalyzer

        analyzer = CompletionAnalyzer()
        prompt = "Output LOOP_COMPLETE when done"

        analysis = analyzer.analyze(prompt)

        assert analysis["has_completion_marker"] is True
        assert analysis["has_loop_complete"] is True

    def test_checked_task_complete_detected(self):
        """Should detect checked [x] TASK_COMPLETE."""
        from ralph_orchestrator.transform.analyzers import CompletionAnalyzer

        analyzer = CompletionAnalyzer()
        prompt = "- [x] TASK_COMPLETE"

        analysis = analyzer.analyze(prompt)

        assert analysis["has_completion_marker"] is True
        assert analysis["has_task_complete"] is True


class TestTransformChangesTracking:
    """Tests for tracking what changed during transformation."""

    def test_changes_list_populated(self):
        """Should track what changes were made."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        result = transformer.transform("Simple task")

        # Should have at least one change recorded
        assert len(result.changes) > 0
        assert "completion marker" in str(result.changes).lower()

    def test_no_changes_when_complete(self):
        """Should have no changes when prompt already complete."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        original = """# Task
Do something

## Completion Status
- [ ] TASK_COMPLETE
"""
        result = transformer.transform(original)

        # No completion marker change should be recorded
        completion_changes = [c for c in result.changes if "completion" in c.lower()]
        assert len(completion_changes) == 0


class TestAnalysisOutput:
    """Tests for analysis dictionary content."""

    def test_analysis_contains_completion_info(self):
        """Analysis should contain completion detection results."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        result = transformer.transform("Simple task")

        assert "has_completion_marker" in result.analysis
        assert "has_completion_section" in result.analysis

    def test_validation_contains_status(self):
        """Validation should contain valid status."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()
        result = transformer.transform("Simple task")

        assert "valid" in result.validation
        assert isinstance(result.validation["valid"], bool)
