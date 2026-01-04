<objective>
Validate the semantic validation system with REAL file content analysis - no mocking.

This is Phase 2 of comprehensive functional validation for ralph-orchestrator.
Tests must create actual files with error patterns and verify detection.
</objective>

<context>
Target module: src/ralph_orchestrator/validation/
Key classes:
- EvidenceChecker: Parses JSON/text for error patterns
- ValidationResult: Success/failure with errors
- OrchestrationPhaseValidator: Directory-level validation

The validation system must:
- Detect {"detail": "Orchestrator not found"} as FAILURE
- Detect {"error": "..."} as FAILURE
- Detect {"status": "fail"} as FAILURE
- Pass valid JSON without error patterns
- Handle malformed JSON gracefully
</context>

<execution_requirements>
Use sequential-thinking MCP for structured analysis.
Use Opus 4.5 model for maximum capability.
Use claude-mem for context preservation.

MANDATORY: Create REAL files in isolated temp directories. No mocking.
</execution_requirements>

<validation_scenarios>
Execute each scenario with real file I/O:

**Scenario 1: Error Pattern Detection - "detail" field**
```python
import tempfile
import json
from pathlib import Path
from ralph_orchestrator.validation import validate_evidence_directory

def test_detail_error_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file with error pattern
        error_file = Path(tmpdir) / "api-response.json"
        error_file.write_text(json.dumps({
            "detail": "Orchestrator not found"
        }))

        result = validate_evidence_directory(tmpdir)

        assert result.success == False, "Should detect 'detail' error"
        assert any("detail" in err.lower() for err in result.errors)

        return {
            "scenario": "detail_error",
            "passed": not result.success,
            "errors_found": result.errors
        }

result = test_detail_error_detection()
```

**Scenario 2: Error Pattern Detection - "error" field**
```python
def test_error_field_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        error_file = Path(tmpdir) / "response.json"
        error_file.write_text(json.dumps({
            "error": "Connection refused",
            "code": 500
        }))

        result = validate_evidence_directory(tmpdir)

        assert result.success == False
        assert any("error" in err.lower() for err in result.errors)

        return {
            "scenario": "error_field",
            "passed": not result.success,
            "errors_found": result.errors
        }

result = test_error_field_detection()
```

**Scenario 3: Error Pattern Detection - "status" fail**
```python
def test_status_fail_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        error_file = Path(tmpdir) / "status.json"
        error_file.write_text(json.dumps({
            "status": "fail",
            "message": "Validation failed"
        }))

        result = validate_evidence_directory(tmpdir)

        assert result.success == False

        return {
            "scenario": "status_fail",
            "passed": not result.success
        }

result = test_status_fail_detection()
```

**Scenario 4: Valid JSON Passes**
```python
def test_valid_json_passes():
    with tempfile.TemporaryDirectory() as tmpdir:
        valid_file = Path(tmpdir) / "valid.json"
        valid_file.write_text(json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "data": {"count": 42}
        }))

        result = validate_evidence_directory(tmpdir)

        assert result.success == True, f"Valid JSON should pass: {result.errors}"

        return {
            "scenario": "valid_json",
            "passed": result.success
        }

result = test_valid_json_passes()
```

**Scenario 5: Text File Error Detection**
```python
def test_text_traceback_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        text_file = Path(tmpdir) / "error.txt"
        text_file.write_text("""
Traceback (most recent call last):
  File "test.py", line 10, in <module>
    raise ValueError("test error")
ValueError: test error
""")

        result = validate_evidence_directory(tmpdir)

        assert result.success == False
        assert any("traceback" in err.lower() for err in result.errors)

        return {
            "scenario": "text_traceback",
            "passed": not result.success
        }

result = test_text_traceback_detection()
```

**Scenario 6: Mixed Directory - Partial Failures**
```python
def test_mixed_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        # One valid file
        valid = Path(tmpdir) / "valid.json"
        valid.write_text(json.dumps({"status": "ok"}))

        # One error file
        error = Path(tmpdir) / "error.json"
        error.write_text(json.dumps({"detail": "not found"}))

        result = validate_evidence_directory(tmpdir)

        # Should fail because of error file
        assert result.success == False

        return {
            "scenario": "mixed_directory",
            "passed": not result.success,
            "errors": result.errors
        }

result = test_mixed_directory()
```

**Scenario 7: Empty Directory Handling**
```python
def test_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_evidence_directory(tmpdir)

        # Empty should pass or warn, not error
        # (no evidence = nothing failed)

        return {
            "scenario": "empty_directory",
            "success": result.success,
            "warnings": result.warnings
        }

result = test_empty_directory()
```

**Scenario 8: Malformed JSON Handling**
```python
def test_malformed_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_json = Path(tmpdir) / "bad.json"
        bad_json.write_text("{not valid json")

        result = validate_evidence_directory(tmpdir)

        # Should handle gracefully - either warn or fail
        # Should NOT crash

        return {
            "scenario": "malformed_json",
            "handled_gracefully": True,  # If we get here, it didn't crash
            "result": result.success,
            "errors": result.errors
        }

result = test_malformed_json()
```
</validation_scenarios>

<success_criteria>
All 8 scenarios must execute without crashes:

| Scenario | Success Condition |
|----------|-------------------|
| detail error | Detected as FAILURE |
| error field | Detected as FAILURE |
| status fail | Detected as FAILURE |
| valid JSON | PASSES validation |
| text traceback | Detected as FAILURE |
| mixed directory | Detected as FAILURE |
| empty directory | Handles gracefully |
| malformed JSON | Handles gracefully |

Functional: 8/8 scenarios complete
Evidence: Save to validation-evidence/functional-02/
</success_criteria>

<output>
1. Execute each scenario with real file operations
2. Create evidence file: `./validation-evidence/functional-02/validation-system.txt`
3. Report structured results:
   ```
   VALIDATION SYSTEM FUNCTIONAL TESTS
   ==================================
   Scenario 1 (detail): PASS/FAIL
   Scenario 2 (error): PASS/FAIL
   Scenario 3 (status): PASS/FAIL
   Scenario 4 (valid): PASS/FAIL
   Scenario 5 (traceback): PASS/FAIL
   Scenario 6 (mixed): PASS/FAIL
   Scenario 7 (empty): PASS/FAIL
   Scenario 8 (malformed): PASS/FAIL

   Overall: X/8 PASS
   ```
4. If any FAIL: Document and iterate
5. If all PASS: Signal ready for Phase 3
</output>

<iteration_protocol>
If ANY scenario fails:
1. Document failure with full context
2. Identify if it's a test issue or code issue
3. Fix the root cause (not the symptom)
4. Re-run failed scenario
5. Repeat until PASS

Maximum 3 iterations per scenario.
</iteration_protocol>
