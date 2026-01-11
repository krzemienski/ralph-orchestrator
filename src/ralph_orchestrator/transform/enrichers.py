"""Enrichers for adding missing elements to prompts.

Each enricher adds a specific type of content to the prompt
based on analysis results.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

# Import TransformContext from the module level to avoid circular imports
# We use string typing for forward reference
if False:  # TYPE_CHECKING equivalent
    from .transformer import TransformContext


class BaseEnricher(ABC):
    """Base class for prompt enrichers."""

    @abstractmethod
    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Enrich the prompt with additional content.

        Args:
            prompt: The prompt text to enrich
            analysis: Analysis results from analyzers
            context: Optional TransformContext with runtime info

        Returns:
            Enriched prompt text
        """
        pass


class CompletionEnricher(BaseEnricher):
    """Adds completion section and marker if missing.

    HIGH PRIORITY enricher - ensures orchestrator can detect completion.
    """

    COMPLETION_TEMPLATE = """

## Completion Status
- [ ] TASK_COMPLETE

When all requirements are satisfied, mark the checkbox above as complete:
`- [x] TASK_COMPLETE`

Or output `LOOP_COMPLETE` to signal the orchestrator to stop.
"""

    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Add completion section if missing.

        Args:
            prompt: Original prompt
            analysis: Must contain has_completion_marker and has_completion_section

        Returns:
            Prompt with completion section added if needed
        """
        # Skip if marker already exists
        if analysis.get("has_completion_marker", False):
            return prompt

        # Add completion section at the end
        return prompt.rstrip() + self.COMPLETION_TEMPLATE


class PathResolutionEnricher(BaseEnricher):
    """Adds runtime context header with working directory.

    HIGH PRIORITY enricher - prevents path hallucination.
    """

    RUNTIME_CONTEXT_TEMPLATE = """<!-- RUNTIME CONTEXT -->
Working Directory: {working_directory}
{task_file_line}{scratchpad_line}<!-- END RUNTIME CONTEXT -->

"""

    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Add runtime context header if context provided.

        Args:
            prompt: Original prompt
            analysis: Not used by this enricher
            context: TransformContext with working_directory

        Returns:
            Prompt with runtime context header prepended
        """
        # Skip if no context provided
        if context is None:
            return prompt

        # Skip if no working directory
        working_dir = getattr(context, 'working_directory', None)
        if not working_dir:
            return prompt

        # Build context lines
        task_file = getattr(context, 'task_file', None)
        task_file_line = f"Task File: {task_file}\n" if task_file else ""

        scratchpad = getattr(context, 'scratchpad_path', None)
        scratchpad_line = f"Scratchpad: {scratchpad}\n" if scratchpad else ""

        # Format header
        header = self.RUNTIME_CONTEXT_TEMPLATE.format(
            working_directory=working_dir,
            task_file_line=task_file_line,
            scratchpad_line=scratchpad_line
        )

        return header + prompt


class ScratchpadEnricher(BaseEnricher):
    """Clears or namespaces scratchpad references.

    HIGH PRIORITY enricher - prevents stale context issues.
    """

    SCRATCHPAD_HINT = """
<!-- SCRATCHPAD NOTE -->
If using a scratchpad file, ensure it is cleared or namespaced for this task.
Previous task context should not carry over.
<!-- END SCRATCHPAD NOTE -->
"""

    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Add scratchpad hint if scratchpad references detected.

        For now, just adds a hint. Future versions could auto-clear.

        Args:
            prompt: Original prompt
            analysis: Not currently used
            context: TransformContext with scratchpad_path

        Returns:
            Prompt with scratchpad hint if relevant
        """
        # Only add hint if context mentions scratchpad
        if context and getattr(context, 'scratchpad_path', None):
            # Insert after runtime context if present, else at start
            if "<!-- END RUNTIME CONTEXT -->" in prompt:
                return prompt.replace(
                    "<!-- END RUNTIME CONTEXT -->",
                    "<!-- END RUNTIME CONTEXT -->" + self.SCRATCHPAD_HINT
                )
            return self.SCRATCHPAD_HINT + prompt

        return prompt


class CheckboxEnricher(BaseEnricher):
    """Converts numbered lists to checkbox format.

    MEDIUM PRIORITY enricher - improves trackability.
    """

    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Convert numbered requirements to checkboxes.

        Args:
            prompt: Original prompt
            analysis: Should contain numbered_items if present

        Returns:
            Prompt with numbered lists converted to checkboxes
        """
        import re

        # Only convert if we have numbered items and no checkboxes
        if not analysis.get("has_numbered_lists", False):
            return prompt

        if analysis.get("has_checkboxes", False):
            return prompt  # Already has checkboxes

        # Convert numbered items to checkboxes
        def replace_numbered(match):
            return f"- [ ] {match.group(1)}"

        return re.sub(r'^\d+\.\s+(.+)$', replace_numbered, prompt, flags=re.MULTILINE)


class SuccessCriteriaEnricher(BaseEnricher):
    """Adds success criteria section if missing.

    MEDIUM PRIORITY enricher - reduces ambiguity.
    """

    SUCCESS_CRITERIA_TEMPLATE = """
## Success Criteria
- Task requirements are fully implemented
- Code executes without errors
- All tests pass (if applicable)
"""

    def enrich(
        self,
        prompt: str,
        analysis: dict,
        context: Optional[Any] = None
    ) -> str:
        """Add success criteria section if missing.

        Args:
            prompt: Original prompt
            analysis: Should contain has_success_criteria

        Returns:
            Prompt with success criteria section added if needed
        """
        if analysis.get("has_success_criteria", False):
            return prompt

        # Insert before completion section if present
        if "## Completion" in prompt:
            return prompt.replace(
                "## Completion",
                self.SUCCESS_CRITERIA_TEMPLATE + "\n## Completion"
            )

        # Otherwise add at end (before completion template would be added)
        return prompt.rstrip() + self.SUCCESS_CRITERIA_TEMPLATE
