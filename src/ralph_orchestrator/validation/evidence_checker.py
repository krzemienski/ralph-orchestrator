# ABOUTME: Semantic content validation for evidence files (JSON/text analysis)
# ABOUTME: Core fix for the broken validation that checked file existence, not content

"""Evidence checker for semantic validation of evidence files.

This module provides the core content analysis that was missing from the original
validation system. Instead of just checking file existence, it parses content
to detect actual errors like {"detail":"Orchestrator not found"}.

Error Patterns Detected:
    - {"detail": "...not found..."} - API 404-style errors
    - {"error": "..."} - Explicit error field
    - {"status": "error"} or {"status": "fail"} - Status-based errors
    - {"is_error": true} - Boolean error indicator
    - {} or null - Empty/null responses
    - Invalid JSON - Parse failures
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base_validator import ValidationResult


logger = logging.getLogger(__name__)


class EvidenceChecker:
    """Semantic content validation for evidence files.

    Analyzes JSON and text files to detect error patterns that indicate
    failed operations, even when the file itself exists.

    Example:
        checker = EvidenceChecker()
        result = checker.check_json_for_errors(Path("api-response.json"))
        if not result.success:
            print(f"Errors detected: {result.errors}")
    """

    # Error patterns to detect in JSON content
    ERROR_PATTERNS: Dict[str, List[str]] = {
        # Field-based patterns: field_name -> error_value_patterns
        "detail": ["not found", "error", "failed", "denied", "unauthorized"],
        "error": [],  # Any value in "error" field is an error
        "message": ["error", "failed", "exception"],
    }

    # Status values that indicate failure
    ERROR_STATUS_VALUES: Set[str] = {
        "error", "fail", "failed", "failure", "exception", "denied"
    }

    # Text patterns that indicate errors (for .txt files)
    TEXT_ERROR_PATTERNS: List[str] = [
        r'"detail"\s*:\s*"[^"]*not found[^"]*"',
        r'"error"\s*:\s*"[^"]*"',
        r'"status"\s*:\s*"(?:error|fail|failed)"',
        r'"is_error"\s*:\s*true',
        r'Connection refused',
        r'ECONNREFUSED',
        r'timeout',
        r'fatal error',
        r'Exception:',
        r'Traceback \(most recent call last\)',
    ]

    def __init__(self):
        """Initialize the evidence checker."""
        self._compiled_text_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.TEXT_ERROR_PATTERNS
        ]

    def check_json_for_errors(self, filepath: Path) -> ValidationResult:
        """Parse JSON file and detect error patterns.

        Analyzes JSON structure to find common error indicators:
        - {"detail": "...not found..."}
        - {"error": "..."}
        - {"status": "error"|"fail"}
        - {"is_error": true}
        - Empty objects or null values

        Args:
            filepath: Path to JSON file to check.

        Returns:
            ValidationResult with success=False if errors detected.
        """
        if not filepath.exists():
            return ValidationResult.from_errors([f"File not found: {filepath}"])

        try:
            content = filepath.read_text()
        except (IOError, OSError) as e:
            return ValidationResult.from_errors([f"Cannot read file {filepath}: {e}"])

        # Try to parse as JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return ValidationResult.from_errors([
                f"Invalid JSON in {filepath.name}: {e}"
            ])

        return self._check_json_data(data, filepath.name)

    def _check_json_data(self, data: Any, source: str = "") -> ValidationResult:
        """Check parsed JSON data for error patterns.

        Args:
            data: Parsed JSON data (dict, list, or primitive).
            source: Source name for error messages.

        Returns:
            ValidationResult indicating if errors were found.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for null response
        if data is None:
            errors.append(f"Null JSON response in {source}")
            return ValidationResult.from_errors(errors)

        # Check for empty object
        if isinstance(data, dict) and len(data) == 0:
            errors.append(f"Empty JSON object in {source}")
            return ValidationResult.from_errors(errors)

        # Check for empty array
        if isinstance(data, list) and len(data) == 0:
            warnings.append(f"Empty JSON array in {source}")

        if isinstance(data, dict):
            # Check for explicit error indicators
            self._check_dict_for_errors(data, source, errors, warnings)

        if errors:
            return ValidationResult.from_errors(errors)

        result = ValidationResult.from_success(warnings if warnings else None)
        return result

    def _check_dict_for_errors(
        self,
        data: Dict[str, Any],
        source: str,
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """Check a dictionary for error patterns.

        Args:
            data: Dictionary to check.
            source: Source name for error messages.
            errors: List to append errors to.
            warnings: List to append warnings to.
        """
        # Check "detail" field (common in FastAPI/REST errors)
        if "detail" in data:
            detail = str(data["detail"]).lower()
            if any(pattern in detail for pattern in self.ERROR_PATTERNS["detail"]):
                errors.append(f"Error in {source}: detail='{data['detail']}'")

        # Check "error" field (any value is an error)
        if "error" in data and data["error"]:
            errors.append(f"Error in {source}: error='{data['error']}'")

        # Check "status" field for error values
        if "status" in data:
            status = str(data["status"]).lower()
            if status in self.ERROR_STATUS_VALUES:
                errors.append(f"Error status in {source}: status='{data['status']}'")

        # Check "is_error" boolean field
        if "is_error" in data and data["is_error"] is True:
            errors.append(f"Error flag in {source}: is_error=true")

        # Check "success" boolean field (False = error)
        if "success" in data and data["success"] is False:
            # Only error if there's no other success indicator
            if "result" not in data or not data["result"]:
                errors.append(f"Failure in {source}: success=false")

        # Check "message" field for error keywords
        if "message" in data:
            message = str(data["message"]).lower()
            if any(pattern in message for pattern in self.ERROR_PATTERNS["message"]):
                warnings.append(f"Possible error in {source}: message='{data['message']}'")

    def check_text_for_errors(self, filepath: Path) -> ValidationResult:
        """Check text file for error patterns.

        Scans text content for patterns that indicate errors, including
        embedded JSON error responses.

        Args:
            filepath: Path to text file to check.

        Returns:
            ValidationResult with success=False if errors detected.
        """
        if not filepath.exists():
            return ValidationResult.from_errors([f"File not found: {filepath}"])

        try:
            content = filepath.read_text(errors="ignore")
        except (IOError, OSError) as e:
            return ValidationResult.from_errors([f"Cannot read file {filepath}: {e}"])

        errors: List[str] = []
        warnings: List[str] = []

        # Check for compiled error patterns
        for pattern in self._compiled_text_patterns:
            match = pattern.search(content)
            if match:
                # Extract matched text for error message
                matched_text = match.group(0)[:100]  # Truncate long matches
                errors.append(
                    f"Error pattern in {filepath.name}: '{matched_text}'"
                )

        # Try to extract and parse any embedded JSON
        json_matches = re.findall(r'\{[^{}]*\}', content)
        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                result = self._check_json_data(data, f"{filepath.name} (embedded)")
                if not result.success:
                    errors.extend(result.errors)
            except json.JSONDecodeError:
                pass  # Not valid JSON, skip

        if errors:
            return ValidationResult.from_errors(errors)

        return ValidationResult.from_success(warnings if warnings else None)

    def check_evidence_freshness(
        self,
        filepath: Path,
        max_age_hours: int = 24,
    ) -> bool:
        """Check if evidence file is fresh (created recently).

        Args:
            filepath: Path to evidence file.
            max_age_hours: Maximum age in hours to be considered fresh.

        Returns:
            True if file is fresh, False if stale or not found.
        """
        if not filepath.exists():
            return False

        try:
            file_mtime = filepath.stat().st_mtime
            age_hours = (time.time() - file_mtime) / 3600

            return age_hours <= max_age_hours
        except OSError:
            return False

    def check_file(self, filepath: Path) -> ValidationResult:
        """Check any evidence file for errors based on extension.

        Automatically selects the appropriate check method based on
        file extension.

        Args:
            filepath: Path to evidence file.

        Returns:
            ValidationResult from appropriate checker.
        """
        suffix = filepath.suffix.lower()

        if suffix == ".json":
            return self.check_json_for_errors(filepath)
        elif suffix in (".txt", ".log", ".md"):
            return self.check_text_for_errors(filepath)
        else:
            # For unknown types, try text check
            return self.check_text_for_errors(filepath)
