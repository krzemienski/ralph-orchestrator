"""Core prompt transformation functionality.

Transforms user prompts into RALF-optimized format by:
1. Analyzing existing structure
2. Enriching with missing elements
3. Validating the result
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from .analyzers import CompletionAnalyzer
from .enrichers import CompletionEnricher, PathResolutionEnricher


@dataclass
class TransformConfig:
    """Configuration for prompt transformation."""
    add_completion_marker: bool = True
    add_path_resolution: bool = True
    add_scratchpad_header: bool = True
    convert_to_checkboxes: bool = False  # MEDIUM priority
    add_success_criteria: bool = False   # MEDIUM priority


@dataclass
class TransformContext:
    """Runtime context for transformation."""
    working_directory: Optional[str] = None
    task_file: Optional[str] = None
    scratchpad_path: Optional[str] = None
    iteration: int = 1


@dataclass
class TransformResult:
    """Result of prompt transformation."""
    original: str
    transformed: str
    analysis: dict = field(default_factory=dict)
    validation: dict = field(default_factory=dict)
    changes: list = field(default_factory=list)


class PromptTransformer:
    """Transforms prompts into RALF-optimized format.

    Pipeline:
    1. ANALYZE: Detect existing structure (sections, checkboxes, completion)
    2. ENRICH: Add missing elements based on analysis
    3. VALIDATE: Ensure result is well-formed
    """

    def __init__(self, config: Optional[TransformConfig] = None):
        """Initialize transformer with optional config."""
        self.config = config or TransformConfig()

        # Initialize analyzers
        self.analyzers = [
            CompletionAnalyzer(),
        ]

        # Initialize enrichers conditionally based on config (ordered by priority)
        self.enrichers = []
        if self.config.add_completion_marker:
            self.enrichers.append(CompletionEnricher())      # HIGH priority
        if self.config.add_path_resolution:
            self.enrichers.append(PathResolutionEnricher())  # HIGH priority

    def transform(
        self,
        prompt: str,
        context: Optional[TransformContext] = None
    ) -> TransformResult:
        """Transform a prompt into RALF-optimized format.

        Args:
            prompt: The original prompt text
            context: Optional runtime context (working directory, etc.)

        Returns:
            TransformResult with original, transformed, analysis, and changes
        """
        # Phase 1: Analyze
        analysis = self._analyze(prompt)

        # Phase 2: Enrich
        enriched = self._enrich(prompt, analysis, context)

        # Phase 3: Validate
        validation = self._validate(enriched)

        # Calculate changes
        changes = self._calculate_changes(prompt, enriched)

        return TransformResult(
            original=prompt,
            transformed=enriched,
            analysis=analysis,
            validation=validation,
            changes=changes
        )

    def _analyze(self, prompt: str) -> dict:
        """Run all analyzers on the prompt."""
        analysis = {}
        for analyzer in self.analyzers:
            analyzer_result = analyzer.analyze(prompt)
            analysis.update(analyzer_result)
        return analysis

    def _enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[TransformContext]
    ) -> str:
        """Run enrichers to add missing elements."""
        enriched = prompt
        for enricher in self.enrichers:
            enriched = enricher.enrich(enriched, analysis, context)
        return enriched

    def _validate(self, prompt: str) -> dict:
        """Validate the transformed prompt."""
        return {
            "valid": True,
            "has_completion_marker": "TASK_COMPLETE" in prompt,
            "warnings": []
        }

    def _calculate_changes(self, original: str, transformed: str) -> list:
        """Calculate what changed between original and transformed."""
        changes = []
        if original != transformed:
            if "TASK_COMPLETE" in transformed and "TASK_COMPLETE" not in original:
                changes.append("Added completion marker")
            if "Working Directory:" in transformed and "Working Directory:" not in original:
                changes.append("Added path resolution header")
        return changes
