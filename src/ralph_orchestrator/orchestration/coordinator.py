#!/usr/bin/env python3
# ABOUTME: CoordinationManager for subagent file-based communication
# ABOUTME: Implements shared context, attempt tracking, and result collection

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class CoordinationManager:
    """Manages file-based coordination between subagents.

    Creates and manages the coordination directory structure:
    .agent/coordination/
    ├── current-attempt.json       # Current attempt metadata
    ├── shared-context.md          # Shared understanding between subagents
    ├── attempt-journal.md         # Full history of attempts
    └── subagent-results/          # Result files from each subagent
        ├── validator-001.json
        ├── researcher-001.json
        └── implementer-001.json
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize CoordinationManager.

        Args:
            base_dir: Base directory for .agent/coordination structure.
                     Defaults to current working directory.
        """
        self.base_dir = base_dir if base_dir is not None else Path.cwd()

    @property
    def coordination_dir(self) -> Path:
        """Path to the coordination directory."""
        return self.base_dir / ".agent" / "coordination"

    @property
    def results_dir(self) -> Path:
        """Path to the subagent results directory."""
        return self.coordination_dir / "subagent-results"

    def init_coordination(self) -> None:
        """Initialize the coordination directory structure.

        Creates .agent/coordination/ and subagent-results/ directories.
        Safe to call multiple times (idempotent).
        """
        self.coordination_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def write_attempt_start(
        self, attempt_number: int, phase: str, criteria: List[str]
    ) -> None:
        """Write current attempt metadata to current-attempt.json.

        Args:
            attempt_number: The attempt number (1-indexed)
            phase: Name of the current phase being worked on
            criteria: List of acceptance criteria for this attempt
        """
        attempt_data = {
            "attempt_number": attempt_number,
            "phase": phase,
            "criteria": criteria,
            "started_at": datetime.now().isoformat(),
        }

        attempt_file = self.coordination_dir / "current-attempt.json"
        attempt_file.write_text(json.dumps(attempt_data, indent=2))

    def get_current_attempt(self) -> Optional[Dict[str, Any]]:
        """Read current attempt metadata.

        Returns:
            Attempt data dictionary or None if no attempt file exists.
        """
        attempt_file = self.coordination_dir / "current-attempt.json"
        if not attempt_file.exists():
            return None

        try:
            return json.loads(attempt_file.read_text())
        except json.JSONDecodeError:
            return None

    def write_shared_context(self, context: Dict[str, Any]) -> None:
        """Write shared context to shared-context.md.

        Args:
            context: Dictionary of context data to share between subagents.
        """
        context_file = self.coordination_dir / "shared-context.md"

        lines = ["# Shared Context", "", f"Last updated: {datetime.now().isoformat()}", ""]

        for key, value in context.items():
            lines.append(f"## {key}")
            if isinstance(value, list):
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append(str(value))
            lines.append("")

        context_file.write_text("\n".join(lines))

    def get_shared_context(self) -> Optional[str]:
        """Read the shared context file.

        Returns:
            Content of shared-context.md or None if file doesn't exist.
        """
        context_file = self.coordination_dir / "shared-context.md"
        if not context_file.exists():
            return None

        return context_file.read_text()

    def write_subagent_result(
        self, subagent_type: str, result_id: str, result: Dict[str, Any]
    ) -> None:
        """Write a subagent result file.

        Args:
            subagent_type: Type of subagent (validator, researcher, etc.)
            result_id: Unique ID for this result (e.g., "001")
            result: Result data dictionary
        """
        result_file = self.results_dir / f"{subagent_type}-{result_id}.json"
        result_file.write_text(json.dumps(result, indent=2))

    def collect_results(self) -> List[Dict[str, Any]]:
        """Collect all subagent result files.

        Returns:
            List of result dictionaries from all subagent result files.
            Invalid JSON files are skipped.
        """
        results = []

        if not self.results_dir.exists():
            return results

        for result_file in self.results_dir.glob("*.json"):
            try:
                data = json.loads(result_file.read_text())
                results.append(data)
            except json.JSONDecodeError:
                # Skip invalid JSON files
                continue

        return results

    def clear_subagent_results(self) -> None:
        """Remove all subagent result files."""
        if not self.results_dir.exists():
            return

        for result_file in self.results_dir.glob("*.json"):
            result_file.unlink()

    def append_to_journal(self, entry: str, attempt: int) -> None:
        """Append an entry to the attempt journal.

        Args:
            entry: Text to append to the journal
            attempt: Attempt number for context
        """
        journal_file = self.coordination_dir / "attempt-journal.md"

        timestamp = datetime.now().isoformat()
        new_entry = f"\n## Attempt {attempt} - {timestamp}\n\n{entry}\n"

        if journal_file.exists():
            current_content = journal_file.read_text()
            journal_file.write_text(current_content + new_entry)
        else:
            header = "# Attempt Journal\n\nRecord of all attempts during this run.\n"
            journal_file.write_text(header + new_entry)
