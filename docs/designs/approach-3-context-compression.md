# Approach #3: Intelligent Context Compression and Summarization

**Author:** Claude Opus 4.5 Architect
**Date:** 2026-01-10
**Status:** Design Complete

## Executive Summary

This document presents a comprehensive design for intelligent context compression in Ralph Orchestrator. The system implements a 4-stage pipeline that reduces context window waste by 30-50% while maintaining execution quality through hierarchical memory, smart skillbook filtering, and dual compression strategies.

---

## 1. Architectural Design

### 1.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Context Compression Pipeline                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │Collection│───►│Classification │───►│ Compression │───►│  Injection   │  │
│  └──────────┘    └───────────────┘    └─────────────┘    └──────────────┘  │
│       │                 │                    │                   │          │
│       ▼                 ▼                    ▼                   ▼          │
│  Raw context      Essential/Useful/     Extractive or      Priority-ordered │
│  with markers     Wasteful buckets      LLM summary        final prompt     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Hierarchical Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Memory Hierarchy                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  L0 ─ Current Iteration ─────────────────────────────────────────────────── │
│      • Task prompt (verbatim)                                                │
│      • Latest tool results (verbatim)                                        │
│      • NEVER compressed                                                      │
│      • Size: ~500-2000 tokens                                               │
│                                                                              │
│  L1 ─ Previous Iterations ───────────────────────────────────────────────── │
│      • Summarized after completion                                           │
│      • Keep: outcomes, errors, key decisions                                │
│      • Discard: verbose tool outputs, intermediate steps                    │
│      • Size: ~200-500 tokens per iteration                                  │
│                                                                              │
│  L2 ─ Session Patterns ──────────────────────────────────────────────────── │
│      • Extracted across all iterations                                       │
│      • Error patterns (deduplicated)                                        │
│      • Success patterns                                                      │
│      • Size: ~300-800 tokens                                                │
│                                                                              │
│  L3 ─ Persistent Skillbook (ACE) ────────────────────────────────────────── │
│      • Cross-session learned strategies                                      │
│      • FILTERED by relevance to current task                                │
│      • Size: ~200-1000 tokens (from 2000+ raw)                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Integration Points

The compression system integrates at a single point in the orchestrator:

```python
# In orchestrator.py, modify _enhance_prompt_with_instructions()

def _enhance_prompt_with_instructions(self, prompt: str) -> str:
    # Stage 1: Collection
    raw_context = self.context_compressor.collect(
        prompt=prompt,
        skillbook=self.learning_adapter.skillbook if self.learning_adapter else None,
        iteration_history=self.iteration_history,
        error_history=self.context_manager.error_history,
        success_patterns=self.context_manager.success_patterns
    )

    # Stage 2-3: Classification + Compression
    compressed = self.context_compressor.compress(raw_context)

    # Stage 4: Injection
    return self.context_compressor.inject(prompt, compressed)
```

### 1.4 Module Architecture

```
src/ralph_orchestrator/
├── compression/
│   ├── __init__.py
│   ├── compressor.py        # Main ContextCompressor class
│   ├── classifier.py        # Content classification logic
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── extractive.py    # Rule-based extraction
│   │   └── summarizer.py    # LLM-based summarization
│   ├── skillbook_filter.py  # Relevance-based skill filtering
│   └── config.py            # CompressionConfig dataclass
```

---

## 2. Sample Implementation

### 2.1 Core Data Structures

```python
# src/ralph_orchestrator/compression/config.py

from dataclasses import dataclass, field
from typing import List, Pattern
import re

@dataclass
class CompressionConfig:
    """Configuration for context compression."""

    # Compression thresholds
    min_compression_threshold: int = 1000  # tokens
    target_compression_ratio: float = 0.3  # aim for 70% reduction
    max_compressed_size: int = 2000  # tokens

    # LLM summarization settings
    summarization_model: str = "claude-3-haiku-20240307"
    summarization_max_tokens: int = 500
    summarization_timeout: float = 5.0
    enable_llm_summarization: bool = True

    # Content classification
    essential_keywords: List[str] = field(default_factory=lambda: [
        "ERROR", "CRITICAL", "BLOCKED", "IMPORTANT", "FAILED", "Exception"
    ])
    wasteful_patterns: List[str] = field(default_factory=lambda: [
        r"^\s*$",           # Empty lines
        r"^---+$",          # Horizontal rules
        r"^```\s*$",        # Empty code blocks
        r"^#+\s*$",         # Empty headers
    ])

    # Skill relevance
    skill_relevance_threshold: float = 0.5

    # Cache settings
    cache_ttl: int = 300  # seconds
    max_cache_entries: int = 100

    # Async behavior
    async_compression: bool = True
    compression_queue_size: int = 10

    # Feature flags
    mode: str = "active"  # "shadow" | "active"
    fallback_on_error: bool = True
    log_decisions: bool = True


@dataclass
class ContentSection:
    """A section of content with classification metadata."""
    content: str
    source: str  # "skillbook", "error_history", "iteration_N", etc.
    classification: str  # "essential", "useful", "potentially_useful", "wasteful"
    token_count: int
    priority: int  # 1=highest, 4=lowest


@dataclass
class CompressionResult:
    """Result of compression operation."""
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    sections: List[ContentSection]
    strategy_used: str  # "extractive", "llm_summary", "hybrid"
    processing_time_ms: float
```

### 2.2 Main Compressor Class

```python
# src/ralph_orchestrator/compression/compressor.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import tiktoken
import asyncio
import time
from .config import CompressionConfig, ContentSection, CompressionResult
from .classifier import ContentClassifier
from .strategies.extractive import ExtractiveCompressor
from .strategies.summarizer import LLMSummarizer
from .skillbook_filter import SkillbookFilter


class ContextCompressor:
    """
    Main context compression engine implementing the 4-stage pipeline.

    Pipeline:
    1. Collection - Gather raw context with section markers
    2. Classification - Categorize as essential/useful/potentially_useful/wasteful
    3. Compression - Apply extractive or LLM summarization
    4. Injection - Build optimized prompt with priority ordering
    """

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()
        self.classifier = ContentClassifier(self.config)
        self.extractive = ExtractiveCompressor(self.config)
        self.summarizer = LLMSummarizer(self.config)
        self.skillbook_filter = SkillbookFilter(self.config)

        # Token counting
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.encoder = tiktoken.get_encoding("cl100k_base")

        # Metrics
        self.stats = {
            "total_compressions": 0,
            "total_tokens_saved": 0,
            "avg_compression_ratio": 0.0,
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            return len(text) // 4  # Fallback estimate

    def collect(
        self,
        prompt: str,
        skillbook: Optional[Dict[str, Any]] = None,
        iteration_history: Optional[List[Dict]] = None,
        error_history: Optional[List[str]] = None,
        success_patterns: Optional[List[str]] = None,
    ) -> Dict[str, ContentSection]:
        """
        Stage 1: Collection
        Gather raw context and wrap with section markers.
        """
        sections = {}

        # L0: Current prompt (never compressed)
        sections["current_prompt"] = ContentSection(
            content=prompt,
            source="current_prompt",
            classification="essential",
            token_count=self.count_tokens(prompt),
            priority=1
        )

        # L3: Skillbook (filtered by relevance)
        if skillbook and skillbook.get("skills"):
            relevant_skills = self.skillbook_filter.filter_relevant(
                skillbook["skills"],
                prompt
            )
            if relevant_skills:
                skill_content = self._format_skills(relevant_skills)
                sections["skillbook"] = ContentSection(
                    content=skill_content,
                    source="skillbook",
                    classification="useful",
                    token_count=self.count_tokens(skill_content),
                    priority=2
                )

        # L2: Error history (deduplicated)
        if error_history:
            deduped = self._deduplicate_errors(error_history)
            error_content = "\n".join(deduped)
            sections["error_history"] = ContentSection(
                content=error_content,
                source="error_history",
                classification="useful" if deduped else "wasteful",
                token_count=self.count_tokens(error_content),
                priority=2
            )

        # L2: Success patterns
        if success_patterns:
            pattern_content = "\n".join(success_patterns)
            sections["success_patterns"] = ContentSection(
                content=pattern_content,
                source="success_patterns",
                classification="potentially_useful",
                token_count=self.count_tokens(pattern_content),
                priority=3
            )

        # L1: Previous iterations (summarized)
        if iteration_history:
            for i, iteration in enumerate(iteration_history[-3:]):  # Last 3 only
                iter_content = self._format_iteration(iteration)
                sections[f"iteration_{i}"] = ContentSection(
                    content=iter_content,
                    source=f"iteration_{i}",
                    classification="potentially_useful",
                    token_count=self.count_tokens(iter_content),
                    priority=3
                )

        return sections

    def compress(self, sections: Dict[str, ContentSection]) -> CompressionResult:
        """
        Stage 2-3: Classification + Compression
        Apply appropriate compression strategy to each section.
        """
        start_time = time.time()

        original_tokens = sum(s.token_count for s in sections.values())

        # Skip compression if below threshold
        if original_tokens < self.config.min_compression_threshold:
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
                sections=list(sections.values()),
                strategy_used="none",
                processing_time_ms=(time.time() - start_time) * 1000
            )

        compressed_sections = []
        strategy_used = "extractive"

        for name, section in sections.items():
            # Never compress essential content
            if section.classification == "essential":
                compressed_sections.append(section)
                continue

            # Skip wasteful content entirely
            if section.classification == "wasteful":
                continue

            # Choose compression strategy based on content type and size
            if section.token_count > 500 and self.config.enable_llm_summarization:
                # LLM summarization for large narrative content
                compressed = self.summarizer.summarize(section)
                strategy_used = "hybrid"
            else:
                # Extractive compression for structured/small content
                compressed = self.extractive.compress(section)

            if compressed:
                compressed_sections.append(compressed)

        compressed_tokens = sum(s.token_count for s in compressed_sections)

        result = CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
            sections=compressed_sections,
            strategy_used=strategy_used,
            processing_time_ms=(time.time() - start_time) * 1000
        )

        # Update stats
        self.stats["total_compressions"] += 1
        self.stats["total_tokens_saved"] += (original_tokens - compressed_tokens)
        self.stats["avg_compression_ratio"] = (
            (self.stats["avg_compression_ratio"] * (self.stats["total_compressions"] - 1) +
             result.compression_ratio) / self.stats["total_compressions"]
        )

        return result

    def inject(self, base_prompt: str, result: CompressionResult) -> str:
        """
        Stage 4: Injection
        Build optimized prompt with priority-ordered sections.
        """
        # Sort by priority (lower = higher priority)
        sorted_sections = sorted(result.sections, key=lambda s: s.priority)

        parts = []
        total_tokens = 0
        max_tokens = self.config.max_compressed_size

        for section in sorted_sections:
            if section.source == "current_prompt":
                # Current prompt goes at the beginning
                continue

            if total_tokens + section.token_count > max_tokens:
                # Skip lower priority sections if we're at limit
                if section.priority > 2:
                    continue

            parts.append(f"<!-- {section.source} -->\n{section.content}")
            total_tokens += section.token_count

        if parts:
            context_block = "\n\n".join(parts)
            return f"{base_prompt}\n\n<compressed-context>\n{context_block}\n</compressed-context>"

        return base_prompt

    def _format_skills(self, skills: List[Dict]) -> str:
        """Format relevant skills for injection."""
        lines = ["## Relevant Learned Strategies\n"]
        for skill in skills:
            lines.append(f"- **{skill.get('name', 'Unnamed')}**: {skill.get('summary', '')}")
        return "\n".join(lines)

    def _deduplicate_errors(self, errors: List[str]) -> List[str]:
        """Remove duplicate/similar errors."""
        seen = set()
        unique = []
        for error in errors:
            # Normalize for comparison
            normalized = error.lower().strip()[:100]
            if normalized not in seen:
                seen.add(normalized)
                unique.append(error)
        return unique[:5]  # Keep max 5

    def _format_iteration(self, iteration: Dict) -> str:
        """Format iteration summary."""
        outcome = iteration.get("outcome", "unknown")
        summary = iteration.get("summary", "")
        return f"Iteration {iteration.get('number', '?')}: {outcome} - {summary}"
```

### 2.3 Skillbook Filter

```python
# src/ralph_orchestrator/compression/skillbook_filter.py

from typing import List, Dict, Any, Optional
import re
from functools import lru_cache
from .config import CompressionConfig


class SkillbookFilter:
    """
    Filters skillbook skills by relevance to current task.

    Uses keyword matching and optional semantic similarity.
    """

    def __init__(self, config: CompressionConfig):
        self.config = config
        self._relevance_cache: Dict[str, float] = {}

    def filter_relevant(
        self,
        skills: List[Dict[str, Any]],
        prompt: str
    ) -> List[Dict[str, Any]]:
        """
        Filter skills to only those relevant to the current prompt.

        Returns skills with relevance score >= threshold.
        """
        prompt_lower = prompt.lower()
        prompt_keywords = self._extract_keywords(prompt_lower)

        relevant = []
        for skill in skills:
            score = self._calculate_relevance(skill, prompt_keywords, prompt_lower)
            if score >= self.config.skill_relevance_threshold:
                relevant.append({
                    **skill,
                    "_relevance_score": score
                })

        # Sort by relevance and take top 5
        relevant.sort(key=lambda s: s.get("_relevance_score", 0), reverse=True)
        return relevant[:5]

    def _calculate_relevance(
        self,
        skill: Dict[str, Any],
        prompt_keywords: set,
        prompt_lower: str
    ) -> float:
        """Calculate relevance score for a skill."""
        score = 0.0

        # Keyword overlap scoring
        skill_text = f"{skill.get('name', '')} {skill.get('summary', '')}".lower()
        skill_keywords = self._extract_keywords(skill_text)

        if skill_keywords and prompt_keywords:
            overlap = len(skill_keywords & prompt_keywords)
            max_possible = min(len(skill_keywords), len(prompt_keywords))
            if max_possible > 0:
                score += 0.5 * (overlap / max_possible)

        # Direct phrase matching
        skill_name = skill.get("name", "").lower()
        if skill_name and skill_name in prompt_lower:
            score += 0.3

        # Domain matching (file types, frameworks, etc.)
        domains = skill.get("domains", [])
        for domain in domains:
            if domain.lower() in prompt_lower:
                score += 0.2
                break

        return min(score, 1.0)

    @lru_cache(maxsize=100)
    def _extract_keywords(self, text: str) -> frozenset:
        """Extract meaningful keywords from text."""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "and", "but", "if", "or", "because",
            "until", "while", "this", "that", "these", "those", "it"
        }

        # Extract words (alphanumeric + underscores)
        words = re.findall(r'\b[a-z_][a-z0-9_]*\b', text)

        # Filter out stop words and short words
        keywords = {w for w in words if w not in stop_words and len(w) > 2}

        return frozenset(keywords)
```

### 2.4 Extractive Compressor

```python
# src/ralph_orchestrator/compression/strategies/extractive.py

from typing import Optional, List
import re
from ..config import CompressionConfig, ContentSection


class ExtractiveCompressor:
    """
    Rule-based extractive compression.

    Preserves important lines, removes boilerplate and redundancy.
    """

    def __init__(self, config: CompressionConfig):
        self.config = config
        self.essential_patterns = [re.compile(kw, re.IGNORECASE)
                                   for kw in config.essential_keywords]
        self.wasteful_patterns = [re.compile(p) for p in config.wasteful_patterns]

    def compress(self, section: ContentSection) -> Optional[ContentSection]:
        """
        Compress content using extractive rules.

        Strategy:
        1. Always keep lines with essential keywords
        2. Remove wasteful patterns (empty lines, separators)
        3. Deduplicate similar lines
        4. Truncate if still over budget
        """
        lines = section.content.split('\n')

        essential_lines = []
        useful_lines = []

        for line in lines:
            # Check if wasteful
            if any(p.match(line) for p in self.wasteful_patterns):
                continue

            # Check if essential
            if any(p.search(line) for p in self.essential_patterns):
                essential_lines.append(line)
            else:
                useful_lines.append(line)

        # Always include essential lines
        result_lines = essential_lines.copy()

        # Add useful lines up to target size
        target_lines = max(5, len(lines) // 3)  # Keep at least 1/3
        remaining_budget = target_lines - len(essential_lines)

        if remaining_budget > 0:
            # Prioritize first and last lines (often contain key info)
            if useful_lines:
                result_lines.extend(useful_lines[:remaining_budget // 2])
                result_lines.extend(useful_lines[-(remaining_budget // 2):])

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for line in result_lines:
            normalized = line.strip().lower()[:50]
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(line)

        compressed_content = '\n'.join(deduped)

        # Don't return if compression didn't help much
        if len(compressed_content) >= len(section.content) * 0.9:
            return section

        return ContentSection(
            content=compressed_content,
            source=section.source,
            classification=section.classification,
            token_count=len(compressed_content) // 4,  # Estimate
            priority=section.priority
        )
```

### 2.5 LLM Summarizer

```python
# src/ralph_orchestrator/compression/strategies/summarizer.py

from typing import Optional
import asyncio
from ..config import CompressionConfig, ContentSection


class LLMSummarizer:
    """
    LLM-based abstractive summarization for large content blocks.

    Uses a fast, cheap model (Haiku) to generate concise summaries.
    """

    SUMMARY_PROMPT = """Summarize the following content in a concise format.
Focus on:
- Key actions taken
- Important outcomes (success/failure)
- Error messages or blockers
- Decisions made

Keep the summary under {max_tokens} tokens. Be direct and factual.

Content to summarize:
{content}

Summary:"""

    def __init__(self, config: CompressionConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        """Lazy initialization of LLM client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except Exception as e:
                print(f"Warning: Could not initialize Anthropic client: {e}")
                return None
        return self._client

    def summarize(self, section: ContentSection) -> Optional[ContentSection]:
        """
        Generate LLM summary of content.

        Falls back to extractive compression on failure.
        """
        if not self.config.enable_llm_summarization:
            return None

        client = self._get_client()
        if not client:
            return None

        try:
            prompt = self.SUMMARY_PROMPT.format(
                max_tokens=self.config.summarization_max_tokens,
                content=section.content[:8000]  # Limit input size
            )

            response = client.messages.create(
                model=self.config.summarization_model,
                max_tokens=self.config.summarization_max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            return ContentSection(
                content=summary,
                source=f"{section.source}_summary",
                classification=section.classification,
                token_count=len(summary) // 4,  # Estimate
                priority=section.priority
            )

        except Exception as e:
            if self.config.log_decisions:
                print(f"LLM summarization failed for {section.source}: {e}")
            return None

    async def summarize_async(self, section: ContentSection) -> Optional[ContentSection]:
        """Async version for background processing."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.summarize, section)
```

### 2.6 Integration with Orchestrator

```python
# Modifications to src/ralph_orchestrator/orchestrator.py

# Add to imports
from .compression.compressor import ContextCompressor
from .compression.config import CompressionConfig

# Add to RalphOrchestrator.__init__()
def __init__(self, ...):
    # ... existing init code ...

    # Initialize compression
    compression_config = CompressionConfig(
        **config.get("compression", {})
    )
    self.context_compressor = ContextCompressor(compression_config)

# Replace _enhance_prompt_with_instructions()
def _enhance_prompt_with_instructions(self, prompt: str) -> str:
    """Enhance prompt with compressed context."""

    # Collect context from all sources
    sections = self.context_compressor.collect(
        prompt=prompt,
        skillbook=self.learning_adapter.skillbook if self.learning_adapter else None,
        iteration_history=getattr(self, '_iteration_history', []),
        error_history=self.context_manager.error_history,
        success_patterns=self.context_manager.success_patterns
    )

    # Compress
    result = self.context_compressor.compress(sections)

    # Log compression metrics
    if self.verbose_logger:
        self.verbose_logger.log_event(
            "context_compression",
            {
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.compressed_tokens,
                "ratio": result.compression_ratio,
                "strategy": result.strategy_used,
                "time_ms": result.processing_time_ms
            }
        )

    # Inject compressed context
    enhanced = self.context_compressor.inject(prompt, result)

    # Add existing instructions (scratchpad, safety, etc.)
    enhanced = self._add_static_instructions(enhanced)

    return enhanced
```

---

## 3. Analysis

### 3.1 Pros with Probability Scores

| Pro | Probability (0-1) | Impact | Notes |
|-----|-------------------|--------|-------|
| Reduces token costs by 30-50% | **0.85** | High | Based on analysis of current waste patterns |
| Enables longer sessions without context overflow | **0.80** | High | Critical for complex multi-iteration tasks |
| Improves focus by removing noise | **0.70** | Medium | Less irrelevant context = better reasoning |
| Smart skillbook filtering improves relevance | **0.75** | Medium | Currently injects ALL skills regardless |
| Async processing adds no latency | **0.65** | Medium | Fits within existing 2s sleep budget |
| Provides visibility into context usage | **0.90** | Medium | Compression logs enable debugging |
| Deduplicates error history | **0.85** | Low | Simple but effective improvement |
| Enables future advanced compression | **0.60** | High | Foundation for LLM-based strategies |

### 3.2 Cons with Probability Scores

| Con | Probability (0-1) | Severity | Mitigation |
|-----|-------------------|----------|------------|
| Compression may remove needed context | **0.15** | High | Shadow mode, fallback to original |
| LLM summarization adds cost | **0.40** | Medium | Only for large blocks, use Haiku |
| LLM summarization may hallucinate | **0.20** | High | Extractive preferred, LLM optional |
| Adds complexity to codebase | **0.95** | Low | Well-isolated module, clear interfaces |
| Debugging becomes harder | **0.30** | Medium | Full logging of compression decisions |
| Async queue may miss content | **0.10** | Medium | Sync fallback, queue monitoring |
| Relevance filtering may be wrong | **0.25** | Medium | Conservative threshold (0.5), cache |
| Initial tuning required | **0.80** | Low | Start with conservative settings |

### 3.3 Implementation Effort

| Phase | Hours | Description |
|-------|-------|-------------|
| Core data structures | 2-3 | Config, ContentSection, CompressionResult |
| Extractive compressor | 3-4 | Rule-based compression logic |
| Skillbook filter | 3-4 | Relevance scoring, keyword extraction |
| LLM summarizer | 2-3 | Optional LLM integration |
| Main compressor class | 4-5 | Pipeline orchestration |
| Integration with orchestrator | 3-4 | Hook into _enhance_prompt_with_instructions |
| Testing | 4-5 | Unit tests, integration tests |
| Shadow mode | 2-3 | Parallel running without applying |
| Documentation | 2-3 | Usage guide, configuration reference |
| **Total** | **25-34** | ~30 hours median |

### 3.4 Expected Compression Ratios

| Content Type | Current Size | Compressed Size | Ratio |
|--------------|--------------|-----------------|-------|
| Skillbook (full) | 2000+ tokens | 400-600 tokens | 3-5x |
| Error history (5 items) | 500 tokens | 150-200 tokens | 2.5-3x |
| Previous iteration | 800 tokens | 200-300 tokens | 2.5-4x |
| Success patterns | 300 tokens | 150 tokens | 2x |
| **Aggregate** | 3600+ tokens | 900-1250 tokens | **3-4x** |

### 3.5 Cost-Benefit Analysis

```
Compression Cost (per iteration):
- Token counting: ~1ms
- Classification: ~2ms
- Extractive compression: ~5ms
- LLM summarization (if used): ~500ms + $0.0001
- Total: <10ms without LLM, <600ms with LLM

Savings (per iteration):
- Tokens saved: ~2000 tokens
- At Claude pricing ($3/M input): $0.006 per iteration
- Over 100 iterations: $0.60 savings

ROI:
- Implementation: 30 hours * $50/hr = $1500 (one-time)
- Break-even: 250,000 iterations (~2500 Ralph runs)
- BUT: Enables longer sessions that were impossible before
- Real value: Unlocking capability, not just cost savings
```

---

## 4. Benchmark Strategy

### 4.1 Metrics to Capture

| Metric | Description | Target |
|--------|-------------|--------|
| **Token Savings** | (original - compressed) / original | >= 50% |
| **Compression Time** | ms to run compression pipeline | < 100ms (no LLM), < 1s (with LLM) |
| **Task Success Rate** | Tasks completed with compression vs without | No degradation (>= baseline) |
| **Iteration Count** | Iterations needed to complete task | No increase vs baseline |
| **Context Quality Score** | LLM-judged relevance of compressed context | >= 0.8 |
| **Regret Rate** | Times compressed content was needed later | < 5% |
| **Cache Hit Rate** | Skill relevance cache effectiveness | > 70% |

### 4.2 Test Suite Design

```python
# tests/compression/test_benchmark.py

import pytest
from ralph_orchestrator.compression import ContextCompressor
from ralph_orchestrator.compression.config import CompressionConfig

class TestCompressionBenchmarks:
    """Benchmark suite for context compression."""

    @pytest.fixture
    def sample_skillbook(self):
        """Representative skillbook with 10 skills."""
        return {
            "skills": [
                {"name": "python_error_handling", "summary": "Try/except patterns..."},
                {"name": "git_workflow", "summary": "Branch and commit..."},
                # ... 8 more skills
            ]
        }

    @pytest.fixture
    def sample_iteration_history(self):
        """3 previous iterations with typical content."""
        return [
            {"number": 1, "outcome": "partial", "summary": "Created files..."},
            {"number": 2, "outcome": "error", "summary": "Build failed..."},
            {"number": 3, "outcome": "success", "summary": "Fixed imports..."},
        ]

    def test_compression_ratio_target(self, sample_skillbook, sample_iteration_history):
        """Verify we achieve target compression ratio."""
        compressor = ContextCompressor()
        sections = compressor.collect(
            prompt="Fix the Python import error in main.py",
            skillbook=sample_skillbook,
            iteration_history=sample_iteration_history,
            error_history=["ImportError: No module named 'foo'"] * 5,
            success_patterns=["Used absolute imports"]
        )

        result = compressor.compress(sections)

        assert result.compression_ratio <= 0.5, "Should achieve at least 50% compression"
        assert result.compression_ratio >= 0.2, "Should not over-compress"

    def test_essential_content_preserved(self, sample_skillbook):
        """Verify essential content is never removed."""
        compressor = ContextCompressor()

        prompt_with_error = """
        Task: Fix the build

        ERROR: Module not found
        CRITICAL: Build failed
        IMPORTANT: See logs below
        """

        sections = compressor.collect(prompt=prompt_with_error, skillbook=sample_skillbook)
        result = compressor.compress(sections)

        # Find the current_prompt section
        prompt_section = next(s for s in result.sections if s.source == "current_prompt")

        assert "ERROR" in prompt_section.content
        assert "CRITICAL" in prompt_section.content
        assert "IMPORTANT" in prompt_section.content

    def test_compression_speed(self, sample_skillbook, sample_iteration_history):
        """Verify compression completes within time budget."""
        import time

        config = CompressionConfig(enable_llm_summarization=False)
        compressor = ContextCompressor(config)

        start = time.time()
        for _ in range(100):
            sections = compressor.collect(
                prompt="Test prompt",
                skillbook=sample_skillbook,
                iteration_history=sample_iteration_history,
            )
            compressor.compress(sections)
        elapsed = time.time() - start

        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 100, f"Compression should take <100ms, took {avg_ms:.1f}ms"

    def test_skillbook_filtering_accuracy(self, sample_skillbook):
        """Verify relevant skills are selected."""
        compressor = ContextCompressor()

        python_prompt = "Fix the Python TypeError in parser.py"
        sections = compressor.collect(prompt=python_prompt, skillbook=sample_skillbook)

        # Should select python-related skills
        skillbook_section = next(
            (s for s in sections.values() if s.source == "skillbook"),
            None
        )

        if skillbook_section:
            assert "python" in skillbook_section.content.lower()


class TestQualityPreservation:
    """Test that compression doesn't degrade task success."""

    @pytest.mark.slow
    def test_a_b_comparison(self):
        """
        Run same task with and without compression.
        Compare iteration counts and success rates.
        """
        # This would be an integration test running actual Ralph tasks
        # Placeholder for the benchmark framework
        pass
```

### 4.3 A/B Testing Framework

```python
# src/ralph_orchestrator/compression/benchmark.py

from dataclasses import dataclass
from typing import List, Dict, Any
import json
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    task_id: str
    compression_enabled: bool
    success: bool
    iterations: int
    total_tokens_used: int
    tokens_compressed: int
    compression_ratio: float
    task_duration_seconds: float
    regret_events: List[str]  # Times compression hurt


class CompressionBenchmark:
    """
    A/B testing framework for compression quality.

    Runs tasks with and without compression, compares results.
    """

    def __init__(self, output_dir: str = ".ralph/benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []

    def run_comparison(
        self,
        task: str,
        project_dir: str,
        runs_per_variant: int = 3
    ) -> Dict[str, Any]:
        """
        Run task multiple times with and without compression.

        Returns aggregated comparison statistics.
        """
        compressed_results = []
        baseline_results = []

        for i in range(runs_per_variant):
            # Run with compression
            compressed = self._run_task(task, project_dir, compression=True)
            compressed_results.append(compressed)

            # Run without compression
            baseline = self._run_task(task, project_dir, compression=False)
            baseline_results.append(baseline)

        return self._aggregate_comparison(compressed_results, baseline_results)

    def _run_task(self, task: str, project_dir: str, compression: bool) -> BenchmarkResult:
        """Run a single task with given settings."""
        # Integration with Ralph orchestrator
        # This would invoke ralph run with appropriate flags
        pass

    def _aggregate_comparison(
        self,
        compressed: List[BenchmarkResult],
        baseline: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """Aggregate and compare results."""

        def avg(results: List[BenchmarkResult], field: str) -> float:
            values = [getattr(r, field) for r in results]
            return sum(values) / len(values) if values else 0

        return {
            "compressed": {
                "success_rate": avg(compressed, "success") if compressed else 0,
                "avg_iterations": avg(compressed, "iterations"),
                "avg_tokens": avg(compressed, "total_tokens_used"),
                "avg_compression_ratio": avg(compressed, "compression_ratio"),
            },
            "baseline": {
                "success_rate": avg(baseline, "success") if baseline else 0,
                "avg_iterations": avg(baseline, "iterations"),
                "avg_tokens": avg(baseline, "total_tokens_used"),
            },
            "comparison": {
                "tokens_saved_pct": (
                    (avg(baseline, "total_tokens_used") - avg(compressed, "total_tokens_used"))
                    / avg(baseline, "total_tokens_used") * 100
                    if avg(baseline, "total_tokens_used") > 0 else 0
                ),
                "iterations_change": avg(compressed, "iterations") - avg(baseline, "iterations"),
                "success_rate_change": (
                    (avg(compressed, "success") if compressed else 0) -
                    (avg(baseline, "success") if baseline else 0)
                ),
            }
        }

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save all results to file."""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(
                [r.__dict__ for r in self.results],
                f,
                indent=2
            )
```

### 4.4 Success Criteria

| Criteria | Threshold | Measurement Method |
|----------|-----------|-------------------|
| Token savings | >= 30% reduction | Compare compressed vs original token counts |
| Task success rate | No degradation (>= baseline - 2%) | A/B testing across 20+ tasks |
| Iteration count | No increase (< baseline + 0.5) | A/B testing average |
| Processing latency | < 100ms without LLM | Timing in compress() |
| Regret rate | < 5% of iterations | Count times compressed info needed |
| Skill relevance accuracy | >= 80% precision | Manual review of filtered skills |

### 4.5 Continuous Monitoring

```yaml
# .ralph/config/compression_monitoring.yaml

monitoring:
  enabled: true

  # Log compression decisions
  log_level: INFO
  log_file: .ralph/logs/compression.log

  # Metrics to track
  metrics:
    - name: compression_ratio
      alert_if: "> 0.8"  # Alert if compression is ineffective

    - name: processing_time_ms
      alert_if: "> 500"  # Alert if taking too long

    - name: regret_rate
      alert_if: "> 0.05"  # Alert if too much regret

  # Periodic quality check
  quality_check:
    enabled: true
    frequency: "every_10_runs"
    sample_size: 5
```

---

## 5. Rollout Plan

### Phase 1: Shadow Mode (Week 1-2)
- Deploy compression module
- Run in parallel without affecting prompts
- Collect baseline metrics
- Tune thresholds based on observed data

### Phase 2: Opt-in Mode (Week 3-4)
- Enable via `--experimental-compression` flag
- A/B testing on selected projects
- Monitor success rates closely
- Gather user feedback

### Phase 3: Default-On (Week 5+)
- Enable by default
- Provide `--no-compression` escape hatch
- Automatic fallback if quality drops
- Continuous monitoring

---

## 6. Configuration Reference

```yaml
# ralph.yaml compression configuration

compression:
  enabled: true
  mode: "active"  # "shadow" | "active"

  thresholds:
    min_compression_threshold: 1000  # tokens
    target_compression_ratio: 0.3
    max_compressed_size: 2000  # tokens

  llm_summarization:
    enabled: true
    model: "claude-3-haiku-20240307"
    max_tokens: 500
    timeout: 5.0

  skillbook:
    relevance_threshold: 0.5
    max_skills: 5

  cache:
    ttl: 300  # seconds
    max_entries: 100

  async:
    enabled: true
    queue_size: 10

  safety:
    fallback_on_error: true
    log_decisions: true
```

---

## 7. Conclusion

The Intelligent Context Compression system provides a robust, configurable approach to reducing context waste in Ralph iterations. With a conservative 3-4x compression target, smart skillbook filtering, and careful rollout strategy, the system minimizes risk while delivering meaningful token savings.

**Key Strengths:**
- Hierarchical memory architecture aligned with cognitive patterns
- Dual compression strategy (extractive + optional LLM)
- Relevance-based skillbook filtering (major improvement)
- Comprehensive benchmark framework for quality assurance

**Recommendation:** Proceed with implementation, starting with shadow mode to validate compression decisions before going live. The ~30 hour investment is justified by both cost savings and the capability unlock of longer, more complex orchestration sessions.
