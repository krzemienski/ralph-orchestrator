"""Prompt transformation module for RALF orchestrator.

This module provides functionality to transform user prompts into
RALF-optimized format with completion markers, path resolution,
and structured sections.

Usage:
    from ralph_orchestrator.transform import PromptTransformer, TransformContext

    transformer = PromptTransformer()
    result = transformer.transform(
        "Create a hello world script",
        context=TransformContext(working_directory="/path/to/project")
    )
    print(result.transformed)
"""

from .transformer import (
    PromptTransformer,
    TransformConfig,
    TransformContext,
    TransformResult,
)

from .analyzers import (
    BaseAnalyzer,
    CompletionAnalyzer,
    SectionAnalyzer,
    CheckboxAnalyzer,
    RequirementsAnalyzer,
)

from .enrichers import (
    BaseEnricher,
    CompletionEnricher,
    PathResolutionEnricher,
    ScratchpadEnricher,
    CheckboxEnricher,
    SuccessCriteriaEnricher,
)

from .validators import (
    TransformValidator,
    validate_completion_marker,
    validate_working_directory,
)

__all__ = [
    # Core classes
    "PromptTransformer",
    "TransformConfig",
    "TransformContext",
    "TransformResult",
    # Analyzers
    "BaseAnalyzer",
    "CompletionAnalyzer",
    "SectionAnalyzer",
    "CheckboxAnalyzer",
    "RequirementsAnalyzer",
    # Enrichers
    "BaseEnricher",
    "CompletionEnricher",
    "PathResolutionEnricher",
    "ScratchpadEnricher",
    "CheckboxEnricher",
    "SuccessCriteriaEnricher",
    # Validators
    "TransformValidator",
    "validate_completion_marker",
    "validate_working_directory",
]
