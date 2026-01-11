# Prompt Transformer Architecture - v1.1

**Created:** 2026-01-11
**Status:** Design Complete - Ready for Implementation
**Feature Code:** RALF-PTRANS

---

## Executive Summary

This document defines the architecture for RALF's Prompt Transformation feature, enabling automatic structuring of user prompts into RALF-optimized format with proper completion markers, checkpoints, and task breakdowns.

**Dual-Mode Operation:**
1. **Auto-Transform Mode**: Transparently transform prompts during orchestration loading
2. **CLI Command Mode**: Explicit `ralph structure` command for manual transformation

---

## Research Synthesis

### Key Findings from Code Analysis

| Component | Location | Relevance |
|-----------|----------|-----------|
| Prompt Loading | `context.py:ContextManager._load_initial_prompt()` | Integration point for auto-mode |
| Prompt Generation | `__main__.py:385-618` (ralph prompt) | CLI pattern reference |
| Completion Detection | `orchestrator.py:1259-1292` | Target format requirements |
| Enhancement | `adapters/base.py:95-203` | Existing transformation pattern |
| Task Extraction | `orchestrator.py:1143-1181` | Checkbox/task parsing patterns |

### Key Findings from Benchmark Analysis

**Patterns That Work:**
- Explicit `- [x] TASK_COMPLETE` marker (100% detection)
- Checkbox-based requirements (`- [ ]` format)
- Clear Success Criteria sections
- Single output file specifications
- Iteration budget hints

**Patterns That Fail:**
- `**Status: COMPLETE**` (NOT detected - wrong format)
- `## Status: COMPLETE` (NOT detected)
- Numbered lists without checkboxes
- Missing completion section
- Stale scratchpad context

### Key Findings from External Research

| Pattern | Source | Application |
|---------|--------|-------------|
| Plan Mode vs Act Mode | Cline | Separate planning from execution in complex prompts |
| Holistic Planning | Bolt | Pre-structure task breakdown before execution |
| Context Engineering | Industry Trend | Focus on structured context over prompt wording |
| State Machine Orchestration | Agentic Best Practices | Explicit states and transitions |

---

## Architecture Design

### Module Structure

```
src/ralph_orchestrator/
├── transform/                    # NEW MODULE
│   ├── __init__.py              # Public API exports
│   ├── transformer.py           # Core PromptTransformer class
│   ├── analyzers.py             # Structure detection analyzers
│   ├── enrichers.py             # Transformation enrichers
│   └── validators.py            # Output validation
├── context.py                   # MODIFIED - add auto-transform hook
└── __main__.py                  # MODIFIED - add CLI command
```

### Core Components

#### 1. PromptTransformer Class

```python
class PromptTransformer:
    """Transform unstructured prompts into RALF-optimized format."""

    def __init__(self, config: TransformConfig = None):
        self.config = config or TransformConfig()
        self.analyzers = [
            SectionAnalyzer(),      # Detect existing sections
            CheckboxAnalyzer(),     # Find checkbox patterns
            RequirementsAnalyzer(), # Parse requirements
            CompletionAnalyzer(),   # Check for completion markers
        ]
        self.enrichers = [
            CompletionEnricher(),       # HIGH: Add completion section
            PathResolutionEnricher(),   # HIGH: Add runtime paths
            ScratchpadEnricher(),       # HIGH: Clear/namespace scratchpad
            CheckboxEnricher(),         # MEDIUM: Convert lists to checkboxes
            SuccessCriteriaEnricher(),  # MEDIUM: Add success criteria
            IterationHintEnricher(),    # LOW: Add iteration budget
        ]

    def transform(self, prompt: str, context: TransformContext = None) -> TransformResult:
        """Transform prompt and return result with metadata."""
        # 1. Analyze current structure
        analysis = self._analyze(prompt)

        # 2. Apply enrichments based on analysis
        enriched = self._enrich(prompt, analysis, context)

        # 3. Validate output
        validation = self._validate(enriched)

        return TransformResult(
            original=prompt,
            transformed=enriched,
            analysis=analysis,
            validation=validation,
            changes=self._diff(prompt, enriched),
        )
```

#### 2. TransformConfig

```python
@dataclass
class TransformConfig:
    """Configuration for prompt transformation."""

    # Feature toggles
    add_completion_section: bool = True     # HIGH priority
    add_path_resolution: bool = True        # HIGH priority
    clear_scratchpad_reference: bool = True # HIGH priority
    convert_to_checkboxes: bool = True      # MEDIUM priority
    add_success_criteria: bool = True       # MEDIUM priority
    add_iteration_hint: bool = False        # LOW priority (off by default)

    # Behavior options
    preserve_custom_sections: bool = True
    completion_marker_format: str = "- [x] TASK_COMPLETE"
    loop_complete_keyword: str = "LOOP_COMPLETE"

    # Auto-mode specific
    auto_transform_enabled: bool = False    # Must be explicitly enabled
    transform_on_load: bool = True          # Transform during ContextManager load

    @classmethod
    def from_ralph_config(cls, ralph_config) -> "TransformConfig":
        """Create from existing RalphConfig."""
        return cls(
            auto_transform_enabled=ralph_config.prompt_auto_transform,
            # ... map other config options
        )
```

#### 3. TransformContext

```python
@dataclass
class TransformContext:
    """Runtime context for transformation."""
    working_directory: Path
    prompt_file: Path
    scratchpad_path: Path = None
    iteration: int = 1
    task_complexity: str = "medium"  # simple, medium, complex
```

#### 4. TransformResult

```python
@dataclass
class TransformResult:
    """Result of prompt transformation."""
    original: str
    transformed: str
    analysis: PromptAnalysis
    validation: ValidationResult
    changes: List[TransformChange]

    @property
    def was_modified(self) -> bool:
        return self.original != self.transformed

    def summary(self) -> str:
        """Human-readable summary of changes."""
        if not self.was_modified:
            return "No transformation needed - prompt already well-structured"
        return f"Applied {len(self.changes)} transformations:\n" + \
               "\n".join(f"  - {c.description}" for c in self.changes)
```

---

## Integration Points

### Auto-Transform Mode

**Location:** `context.py:ContextManager`

```python
class ContextManager:
    def __init__(self, config: RalphConfig):
        self.config = config
        # NEW: Initialize transformer if auto-mode enabled
        if config.prompt_auto_transform:
            self.transformer = PromptTransformer(
                TransformConfig.from_ralph_config(config)
            )
        else:
            self.transformer = None

    def _load_initial_prompt(self) -> str:
        """Load and optionally transform the initial prompt."""
        prompt = self.prompt_file.read_text()

        # NEW: Auto-transform if enabled
        if self.transformer:
            context = TransformContext(
                working_directory=self.config.working_directory,
                prompt_file=self.prompt_file,
                scratchpad_path=self.config.scratchpad_path,
            )
            result = self.transformer.transform(prompt, context)

            if result.was_modified:
                logger.info(f"Auto-transformed prompt: {result.summary()}")
                # Optionally write back to file for visibility
                if self.config.prompt_transform_write_back:
                    self.prompt_file.write_text(result.transformed)
                return result.transformed

        return prompt
```

### CLI Command Mode

**Location:** `__main__.py`

```python
# Add to argument parser (after line ~520)
structure_parser = subparsers.add_parser(
    'structure',
    help='Transform prompt into RALF-optimized format'
)
structure_parser.add_argument(
    'input',
    help='Input prompt file or text'
)
structure_parser.add_argument(
    '-o', '--output',
    help='Output file (default: overwrite input or stdout)'
)
structure_parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show changes without applying'
)
structure_parser.add_argument(
    '--no-completion',
    action='store_true',
    help='Skip adding completion section'
)
structure_parser.add_argument(
    '--no-checkboxes',
    action='store_true',
    help='Skip converting to checkboxes'
)
structure_parser.add_argument(
    '--minimal',
    action='store_true',
    help='Only add critical elements (completion marker)'
)
structure_parser.add_argument(
    '--json',
    action='store_true',
    help='Output transformation result as JSON'
)

# Handler function
async def handle_structure(args):
    """Handle ralph structure command."""
    from ralph_orchestrator.transform import PromptTransformer, TransformConfig

    # Load input
    if Path(args.input).exists():
        prompt = Path(args.input).read_text()
        input_path = Path(args.input)
    else:
        prompt = args.input  # Treat as literal text
        input_path = None

    # Build config from flags
    config = TransformConfig(
        add_completion_section=not args.no_completion,
        convert_to_checkboxes=not args.no_checkboxes,
        add_path_resolution=not args.minimal,
        add_success_criteria=not args.minimal,
    )

    # Transform
    transformer = PromptTransformer(config)
    context = TransformContext(
        working_directory=Path.cwd(),
        prompt_file=input_path or Path("PROMPT.md"),
    )
    result = transformer.transform(prompt, context)

    # Output
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif args.dry_run:
        print("=== TRANSFORMATION PREVIEW ===")
        print(result.summary())
        print("\n=== TRANSFORMED PROMPT ===")
        print(result.transformed)
    else:
        output_path = Path(args.output) if args.output else input_path
        if output_path:
            output_path.write_text(result.transformed)
            print(f"Transformed prompt written to {output_path}")
            print(result.summary())
        else:
            print(result.transformed)
```

---

## Transformation Pipeline

### Stage 1: Analysis

```python
class PromptAnalysis:
    """Result of analyzing prompt structure."""
    has_requirements_section: bool
    has_success_criteria: bool
    has_completion_section: bool
    has_completion_marker: bool          # The actual [x] TASK_COMPLETE
    has_loop_complete_instruction: bool  # Tells agent to output LOOP_COMPLETE
    checkbox_count: int
    numbered_list_count: int
    detected_sections: List[str]
    estimated_complexity: str  # simple, medium, complex
    issues: List[str]          # Problems found
```

### Stage 2: Enrichment

Each enricher follows this interface:

```python
class BaseEnricher(ABC):
    @abstractmethod
    def should_apply(self, analysis: PromptAnalysis) -> bool:
        """Check if this enricher should run."""
        pass

    @abstractmethod
    def apply(self, prompt: str, analysis: PromptAnalysis, context: TransformContext) -> str:
        """Apply the enrichment and return modified prompt."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this enricher does."""
        pass
```

**CompletionEnricher** (HIGH Priority):
```python
class CompletionEnricher(BaseEnricher):
    def should_apply(self, analysis: PromptAnalysis) -> bool:
        return not analysis.has_completion_section

    def apply(self, prompt: str, analysis: PromptAnalysis, context: TransformContext) -> str:
        completion_section = """
## Completion Status
- [ ] TASK_COMPLETE

When all requirements are satisfied, mark the checkbox above and output LOOP_COMPLETE.
"""
        return prompt + "\n" + completion_section

    @property
    def description(self) -> str:
        return "Added completion section with TASK_COMPLETE marker"
```

**PathResolutionEnricher** (HIGH Priority):
```python
class PathResolutionEnricher(BaseEnricher):
    def should_apply(self, analysis: PromptAnalysis) -> bool:
        return True  # Always add runtime context

    def apply(self, prompt: str, analysis: PromptAnalysis, context: TransformContext) -> str:
        header = f"""<!-- RUNTIME CONTEXT -->
Working Directory: {context.working_directory}
Task File: {context.prompt_file}
Scratchpad: {context.scratchpad_path or '.agent/scratchpad.md'}
<!-- END RUNTIME CONTEXT -->

"""
        return header + prompt

    @property
    def description(self) -> str:
        return "Added runtime path resolution header"
```

**CheckboxEnricher** (MEDIUM Priority):
```python
class CheckboxEnricher(BaseEnricher):
    def should_apply(self, analysis: PromptAnalysis) -> bool:
        return analysis.numbered_list_count > 0 and analysis.checkbox_count == 0

    def apply(self, prompt: str, analysis: PromptAnalysis, context: TransformContext) -> str:
        # Convert numbered lists to checkboxes
        import re
        pattern = r'^(\s*)(\d+)\.\s+(.+)$'
        def replace(match):
            indent, num, text = match.groups()
            return f"{indent}- [ ] {text}"
        return re.sub(pattern, replace, prompt, flags=re.MULTILINE)

    @property
    def description(self) -> str:
        return "Converted numbered lists to checkbox format"
```

### Stage 3: Validation

```python
class ValidationResult:
    """Result of validating transformed prompt."""
    is_valid: bool
    has_checkbox: bool
    has_completion_marker: bool
    has_testable_criteria: bool
    warnings: List[str]

    @classmethod
    def validate(cls, prompt: str) -> "ValidationResult":
        has_checkbox = "- [ ]" in prompt or "- [x]" in prompt
        has_completion = "TASK_COMPLETE" in prompt
        has_loop_complete = "LOOP_COMPLETE" in prompt

        warnings = []
        if not has_checkbox:
            warnings.append("No checkboxes found - agent cannot track progress")
        if not has_completion:
            warnings.append("No TASK_COMPLETE marker - completion may not be detected")
        if not has_loop_complete:
            warnings.append("No LOOP_COMPLETE instruction - agent may not signal completion")

        return cls(
            is_valid=has_checkbox and has_completion,
            has_checkbox=has_checkbox,
            has_completion_marker=has_completion,
            has_testable_criteria=bool(re.search(r'(success|criteria|test|verify)', prompt, re.I)),
            warnings=warnings,
        )
```

---

## Configuration Integration

### RalphConfig Extensions

```python
# In main.py or config.py
@dataclass
class RalphConfig:
    # ... existing fields ...

    # NEW: Prompt transformation settings
    prompt_auto_transform: bool = False      # Enable auto-transform mode
    prompt_transform_write_back: bool = False # Write transformed prompt back to file
    prompt_transform_config: dict = None      # Override transform config options
```

### CLI Flag Extensions

```bash
# Enable auto-transform for a run
ralph run examples/task.md --auto-transform

# Enable auto-transform AND write back (for debugging/visibility)
ralph run examples/task.md --auto-transform --transform-write-back

# Standalone structure command
ralph structure examples/task.md --dry-run
ralph structure examples/task.md -o structured_task.md
ralph structure "Create a hello world script" -o PROMPT.md
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_transform.py

def test_completion_enricher_adds_section():
    enricher = CompletionEnricher()
    prompt = "## Requirements\n- Create file"
    analysis = PromptAnalysis(has_completion_section=False)
    result = enricher.apply(prompt, analysis, mock_context)
    assert "TASK_COMPLETE" in result
    assert "LOOP_COMPLETE" in result

def test_checkbox_enricher_converts_numbered_list():
    enricher = CheckboxEnricher()
    prompt = "1. First task\n2. Second task"
    analysis = PromptAnalysis(numbered_list_count=2, checkbox_count=0)
    result = enricher.apply(prompt, analysis, mock_context)
    assert "- [ ] First task" in result
    assert "- [ ] Second task" in result

def test_transformer_full_pipeline():
    transformer = PromptTransformer()
    prompt = "Create a hello world script in Python"
    result = transformer.transform(prompt, mock_context)
    assert result.was_modified
    assert result.validation.is_valid
    assert "TASK_COMPLETE" in result.transformed
```

### Integration Tests

```python
# tests/test_transform_integration.py

async def test_auto_transform_during_orchestration():
    config = RalphConfig(
        prompt_auto_transform=True,
        max_iterations=3,
    )
    orchestrator = Orchestrator(config)
    # Run with minimal prompt
    result = await orchestrator.run("examples/minimal.md")
    # Should complete due to proper completion detection
    assert result.iterations < config.max_iterations
```

### Benchmark Validation

Run existing tier benchmarks with auto-transform enabled:
- **Target:** Reduce average iterations by 40%
- **Target:** 100% completion detection rate
- **Target:** 0 path hallucination failures

---

## Success Metrics

| Metric | Baseline (v1.0) | Target (v1.1) | Measurement |
|--------|-----------------|---------------|-------------|
| Completion detection rate | 75% | 100% | Benchmark suite |
| Avg iterations to completion | 2.8 | 1.5 | Benchmark suite |
| Path discovery failures | 3.2/run | 0 | Log analysis |
| Prompts requiring manual fix | 40% | 5% | User feedback |
| CLI usability score | N/A | 4.5/5 | User testing |

---

## Implementation Phases

### Phase 7: Core Transformer Module (4-6 hours)
- Create `transform/` module structure
- Implement `PromptTransformer` class
- Implement analyzers (Section, Checkbox, Requirements, Completion)
- Implement HIGH priority enrichers (Completion, PathResolution, Scratchpad)
- Add unit tests

### Phase 8: CLI Command Integration (2-3 hours)
- Add `ralph structure` command to `__main__.py`
- Implement argument parsing
- Add dry-run and output options
- Add CLI tests

### Phase 9: Auto-Transform Integration (2-3 hours)
- Modify `ContextManager` for auto-transform hook
- Add `--auto-transform` CLI flag
- Add transform-write-back option
- Integration tests

### Phase 10: MEDIUM Priority Enrichers (2-3 hours)
- Implement `CheckboxEnricher`
- Implement `SuccessCriteriaEnricher`
- Add `IterationHintEnricher` (LOW priority, off by default)
- Extended tests

### Phase 11: Validation & Benchmarking (3-4 hours)
- Run full benchmark suite with auto-transform
- Measure improvement metrics
- Document results
- Fix any issues discovered

---

## Appendix: Example Transformations

### Input: Minimal Prompt
```markdown
Create a Python script that prints "Hello World"
```

### Output: RALF-Optimized Prompt
```markdown
<!-- RUNTIME CONTEXT -->
Working Directory: /Users/nick/Desktop/ralph-orchestrator
Task File: examples/hello.md
Scratchpad: .agent/scratchpad.md
<!-- END RUNTIME CONTEXT -->

Create a Python script that prints "Hello World"

## Requirements
- [ ] Create Python script file
- [ ] Print "Hello World" message
- [ ] Verify script runs correctly

## Success Criteria
- Script executes without error: `python hello.py`
- Output contains: "Hello World"

## Completion Status
- [ ] TASK_COMPLETE

When all requirements are satisfied, mark the checkbox above and output LOOP_COMPLETE.
```

---

## References

- [Prompt Pattern Analysis](../analysis/PROMPT_PATTERN_ANALYSIS.md)
- [RALF Context Optimization Brief](../../.planning/BRIEF.md)
- [v1.0 Roadmap](../../.planning/ROADMAP.md)
- [Cline Agent Best Practices](https://docs.cline.bot/improving-your-prompting-skills)
- [Context Engineering for Agents](https://www.prompthub.us/blog/prompt-engineering-for-ai-agents)
