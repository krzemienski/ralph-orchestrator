"""Analyzers for detecting existing prompt structure.

Each analyzer examines a specific aspect of the prompt and returns
analysis results that inform the enrichers.
"""
import re
from abc import ABC, abstractmethod
from typing import Any


class BaseAnalyzer(ABC):
    """Base class for prompt analyzers."""

    @abstractmethod
    def analyze(self, prompt: str) -> dict:
        """Analyze the prompt and return findings.

        Args:
            prompt: The prompt text to analyze

        Returns:
            Dictionary of analysis results
        """
        pass


class CompletionAnalyzer(BaseAnalyzer):
    """Analyzes completion markers and sections in prompts.

    Detects:
    - TASK_COMPLETE checkbox marker
    - LOOP_COMPLETE keyword
    - Completion/Status sections
    """

    # Patterns for completion markers
    TASK_COMPLETE_PATTERN = re.compile(
        r'-\s*\[\s*[xX\s]?\s*\]\s*TASK_COMPLETE',
        re.IGNORECASE
    )
    LOOP_COMPLETE_PATTERN = re.compile(r'LOOP_COMPLETE', re.IGNORECASE)
    COMPLETION_SECTION_PATTERN = re.compile(
        r'^#+\s*(Completion|Completion Status|Status)\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    def analyze(self, prompt: str) -> dict:
        """Analyze prompt for completion markers.

        Args:
            prompt: The prompt text to analyze

        Returns:
            Dictionary with:
            - has_completion_marker: bool
            - has_loop_complete: bool
            - has_completion_section: bool
            - marker_location: Optional line number
        """
        has_task_complete = bool(self.TASK_COMPLETE_PATTERN.search(prompt))
        has_loop_complete = bool(self.LOOP_COMPLETE_PATTERN.search(prompt))
        has_completion_section = bool(self.COMPLETION_SECTION_PATTERN.search(prompt))

        # Find marker location if present
        marker_location = None
        if has_task_complete:
            for i, line in enumerate(prompt.split('\n'), 1):
                if self.TASK_COMPLETE_PATTERN.search(line):
                    marker_location = i
                    break

        return {
            "has_completion_marker": has_task_complete or has_loop_complete,
            "has_loop_complete": has_loop_complete,
            "has_task_complete": has_task_complete,
            "has_completion_section": has_completion_section,
            "marker_location": marker_location
        }


class SectionAnalyzer(BaseAnalyzer):
    """Analyzes markdown section structure in prompts."""

    SECTION_PATTERN = re.compile(r'^(#+)\s*(.+)$', re.MULTILINE)

    def analyze(self, prompt: str) -> dict:
        """Analyze prompt sections.

        Returns:
            Dictionary with:
            - sections: List of (level, title) tuples
            - has_requirements: bool
            - has_success_criteria: bool
        """
        sections = []
        for match in self.SECTION_PATTERN.finditer(prompt):
            level = len(match.group(1))
            title = match.group(2).strip()
            sections.append((level, title))

        section_titles = [s[1].lower() for s in sections]

        return {
            "sections": sections,
            "has_requirements": any("requirement" in t for t in section_titles),
            "has_success_criteria": any(
                "success" in t or "criteria" in t for t in section_titles
            ),
            "section_count": len(sections)
        }


class CheckboxAnalyzer(BaseAnalyzer):
    """Analyzes checkbox usage in prompts."""

    CHECKBOX_PATTERN = re.compile(r'-\s*\[\s*[xX\s]?\s*\]\s*(.+)$', re.MULTILINE)
    NUMBERED_LIST_PATTERN = re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE)

    def analyze(self, prompt: str) -> dict:
        """Analyze checkbox and list usage.

        Returns:
            Dictionary with:
            - checkboxes: List of checkbox items
            - checked_count: Number of checked items
            - unchecked_count: Number of unchecked items
            - numbered_lists: List of numbered items (conversion candidates)
        """
        checkboxes = []
        checked_count = 0
        unchecked_count = 0

        for match in self.CHECKBOX_PATTERN.finditer(prompt):
            item = match.group(1).strip()
            is_checked = 'x' in match.group(0).lower().split(']')[0]
            checkboxes.append({"item": item, "checked": is_checked})
            if is_checked:
                checked_count += 1
            else:
                unchecked_count += 1

        numbered_items = self.NUMBERED_LIST_PATTERN.findall(prompt)

        return {
            "checkboxes": checkboxes,
            "checked_count": checked_count,
            "unchecked_count": unchecked_count,
            "has_checkboxes": len(checkboxes) > 0,
            "numbered_items": numbered_items,
            "has_numbered_lists": len(numbered_items) > 0
        }


class RequirementsAnalyzer(BaseAnalyzer):
    """Analyzes requirements structure in prompts."""

    def analyze(self, prompt: str) -> dict:
        """Analyze requirements formatting.

        Returns:
            Dictionary with:
            - has_requirements_section: bool
            - requirements_format: 'checkbox' | 'numbered' | 'bullet' | None
            - requirement_count: int
        """
        # Check for requirements section
        has_section = bool(re.search(
            r'^#+\s*Requirements?\s*$',
            prompt,
            re.MULTILINE | re.IGNORECASE
        ))

        # Determine format
        req_format = None
        if re.search(r'-\s*\[\s*[xX\s]?\s*\]', prompt):
            req_format = "checkbox"
        elif re.search(r'^\d+\.\s+', prompt, re.MULTILINE):
            req_format = "numbered"
        elif re.search(r'^-\s+\w', prompt, re.MULTILINE):
            req_format = "bullet"

        # Count requirements (rough estimate)
        req_count = 0
        if req_format == "checkbox":
            req_count = len(re.findall(r'-\s*\[\s*[xX\s]?\s*\]', prompt))
        elif req_format == "numbered":
            req_count = len(re.findall(r'^\d+\.\s+', prompt, re.MULTILINE))
        elif req_format == "bullet":
            req_count = len(re.findall(r'^-\s+\w', prompt, re.MULTILINE))

        return {
            "has_requirements_section": has_section,
            "requirements_format": req_format,
            "requirement_count": req_count
        }
