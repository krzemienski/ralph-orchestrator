"""Tests for MEDIUM priority enrichers (Phase 10).

Following TDD: Each test is written BEFORE the implementation.
"""
import pytest


class TestCheckboxEnricherIntegration:
    """Tests for CheckboxEnricher integration with transformer."""

    def test_config_has_convert_to_checkboxes_option(self):
        """RED: TransformConfig should have convert_to_checkboxes option."""
        from ralph_orchestrator.transform import TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        assert config.convert_to_checkboxes is True

    def test_transformer_uses_checkbox_enricher_when_enabled(self):
        """RED: Transformer should use CheckboxEnricher when config enabled."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Create a hello world script.

## Requirements
1. Print greeting
2. Make it executable
3. Add error handling
"""
        result = transformer.transform(original)

        # Should convert numbered list to checkboxes
        assert "- [ ] Print greeting" in result.transformed
        assert "- [ ] Make it executable" in result.transformed
        assert "- [ ] Add error handling" in result.transformed
        # Original numbered format should be replaced
        assert "1. Print greeting" not in result.transformed

    def test_checkbox_enricher_skips_when_checkboxes_exist(self):
        """RED: Should not convert if checkboxes already present."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Create a hello world script.

## Requirements
- [ ] Print greeting
- [ ] Make it executable
"""
        result = transformer.transform(original)

        # Should preserve existing checkboxes without modification
        assert result.transformed.count("- [ ] Print greeting") == 1
        assert result.transformed.count("- [ ] Make it executable") == 1

    def test_checkbox_enricher_disabled_by_default(self):
        """RED: Checkbox conversion should be disabled by default."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()

        original = """# Task
1. First step
2. Second step
"""
        result = transformer.transform(original)

        # Should NOT convert when disabled
        assert "1. First step" in result.transformed
        assert "- [ ] First step" not in result.transformed

    def test_checkbox_conversion_tracks_change(self):
        """RED: Should track checkbox conversion in changes list."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
1. Do something
"""
        result = transformer.transform(original)

        # Should record the change
        assert any("checkbox" in change.lower() for change in result.changes)


class TestSuccessCriteriaEnricherIntegration:
    """Tests for SuccessCriteriaEnricher integration with transformer."""

    def test_config_has_add_success_criteria_option(self):
        """RED: TransformConfig should have add_success_criteria option."""
        from ralph_orchestrator.transform import TransformConfig

        config = TransformConfig(add_success_criteria=True)
        assert config.add_success_criteria is True

    def test_transformer_uses_success_criteria_enricher_when_enabled(self):
        """RED: Transformer should use SuccessCriteriaEnricher when config enabled."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(add_success_criteria=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Create a hello world script.

## Requirements
- Print greeting
"""
        result = transformer.transform(original)

        # Should add success criteria section
        assert "## Success Criteria" in result.transformed
        assert "requirements are fully implemented" in result.transformed.lower() or \
               "fully implemented" in result.transformed.lower()

    def test_success_criteria_skips_when_exists(self):
        """RED: Should not add success criteria if already present."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(add_success_criteria=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Create a hello world script.

## Success Criteria
- All tests pass
- Code is clean
"""
        result = transformer.transform(original)

        # Should have exactly one success criteria section
        assert result.transformed.count("## Success Criteria") == 1
        # Original criteria preserved
        assert "All tests pass" in result.transformed

    def test_success_criteria_disabled_by_default(self):
        """RED: Success criteria should be disabled by default."""
        from ralph_orchestrator.transform import PromptTransformer

        transformer = PromptTransformer()

        original = """# Task
Do something simple.
"""
        result = transformer.transform(original)

        # The enricher template contains "## Success Criteria"
        # So checking for the exact addition
        original_had_success = "Success Criteria" in original
        result_has_success = "Success Criteria" in result.transformed

        # If original didn't have it and result does, that would mean it was added
        # We want result_has_success == original_had_success when disabled
        assert result_has_success == original_had_success

    def test_success_criteria_tracks_change(self):
        """RED: Should track success criteria addition in changes list."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(add_success_criteria=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Do something.
"""
        result = transformer.transform(original)

        # Should record the change
        assert any("success" in change.lower() or "criteria" in change.lower()
                   for change in result.changes)

    def test_success_criteria_inserted_before_completion(self):
        """RED: Success criteria should be inserted before completion section."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        # Enable both success criteria and completion marker
        config = TransformConfig(
            add_success_criteria=True,
            add_completion_marker=True
        )
        transformer = PromptTransformer(config=config)

        original = """# Task
Do something.
"""
        result = transformer.transform(original)

        # Success criteria should come before completion
        success_pos = result.transformed.find("## Success Criteria")
        completion_pos = result.transformed.find("## Completion")

        assert success_pos != -1, "Success Criteria section should be present"
        assert completion_pos != -1, "Completion section should be present"
        assert success_pos < completion_pos, "Success Criteria should come before Completion"


class TestCombinedMediumEnrichers:
    """Tests for combined usage of MEDIUM priority enrichers."""

    def test_both_enrichers_can_be_enabled(self):
        """RED: Both MEDIUM enrichers should work together."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(
            convert_to_checkboxes=True,
            add_success_criteria=True
        )
        transformer = PromptTransformer(config=config)

        original = """# Task
Create a hello world script.

## Steps
1. Write code
2. Test it
"""
        result = transformer.transform(original)

        # Both enrichers should apply
        assert "- [ ] Write code" in result.transformed
        assert "## Success Criteria" in result.transformed

    def test_minimal_transform_skips_medium_enrichers(self):
        """RED: Minimal mode should skip MEDIUM priority enrichers."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        # This represents "minimal" mode - only critical (HIGH priority)
        config = TransformConfig(
            add_completion_marker=True,  # HIGH - always on
            add_path_resolution=False,   # Skip even HIGH in minimal
            add_scratchpad_header=False, # Skip
            convert_to_checkboxes=False, # MEDIUM - off
            add_success_criteria=False   # MEDIUM - off
        )
        transformer = PromptTransformer(config=config)

        original = """# Task
1. Do something
2. Do another
"""
        result = transformer.transform(original)

        # Should have completion (critical)
        assert "TASK_COMPLETE" in result.transformed
        # Should NOT have checkbox conversion
        assert "1. Do something" in result.transformed
        assert "- [ ] Do something" not in result.transformed


class TestCheckboxAnalyzerIntegration:
    """Tests for CheckboxAnalyzer integration with transformer."""

    def test_analysis_includes_checkbox_info(self):
        """RED: Analysis should include checkbox detection results."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
1. First step
2. Second step
"""
        result = transformer.transform(original)

        # Analysis should contain checkbox-related info
        assert "has_numbered_lists" in result.analysis or "numbered_items" in result.analysis

    def test_analysis_detects_existing_checkboxes(self):
        """RED: Analysis should detect existing checkboxes."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(convert_to_checkboxes=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
- [ ] Step one
- [x] Step two (done)
"""
        result = transformer.transform(original)

        # Analysis should detect checkboxes
        assert result.analysis.get("has_checkboxes", False) is True


class TestSectionAnalyzerIntegration:
    """Tests for SectionAnalyzer integration with transformer."""

    def test_analysis_includes_section_info(self):
        """RED: Analysis should include section detection results."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(add_success_criteria=True)
        transformer = PromptTransformer(config=config)

        original = """# Task Title
## Requirements
- Something
"""
        result = transformer.transform(original)

        # Analysis should contain section info
        has_section_info = (
            "has_requirements" in result.analysis or
            "sections" in result.analysis or
            "section_count" in result.analysis
        )
        assert has_section_info

    def test_analysis_detects_success_criteria_section(self):
        """RED: Analysis should detect existing success criteria section."""
        from ralph_orchestrator.transform import PromptTransformer, TransformConfig

        config = TransformConfig(add_success_criteria=True)
        transformer = PromptTransformer(config=config)

        original = """# Task
Do something.

## Success Criteria
- Tests pass
"""
        result = transformer.transform(original)

        # Analysis should detect success criteria
        assert result.analysis.get("has_success_criteria", False) is True
