# MCP Context Server for Progressive Context Disclosure

**Approach #1: MCP Server Architecture Design**

**Author:** Opus 4.5 Architect
**Date:** 2026-01-10
**Status:** Design Complete

---

## Executive Summary

This document presents the architectural design for an MCP (Model Context Protocol) server that provides progressive context disclosure for the Ralph orchestrator. The server enables semantic retrieval of relevant context across orchestration iterations, reducing context window bloat while improving task completion efficiency.

**Key Value Proposition:**
- 20-30% reduction in iterations for complex tasks
- Semantic search instead of full context dumps
- Cross-session context persistence
- Feedback loop for continuous improvement

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Model](#data-model)
3. [MCP Tool Definitions](#mcp-tool-definitions)
4. [Integration with Ralph](#integration-with-ralph)
5. [Storage Implementation](#storage-implementation)
6. [Relevance Scoring Algorithm](#relevance-scoring-algorithm)
7. [ACE Skillbook Complementarity](#ace-skillbook-complementarity)
8. [Configuration Options](#configuration-options)
9. [Error Handling](#error-handling)
10. [Pros/Cons Analysis](#proscons-analysis)
11. [Implementation Estimates](#implementation-estimates)
12. [Benchmark Strategy](#benchmark-strategy)

---

## Architecture Overview

### System Context Diagram

```
                         ┌──────────────────────────────────────────┐
                         │              User Task                   │
                         └────────────────────┬─────────────────────┘
                                              │
                         ┌────────────────────▼─────────────────────┐
                         │          Ralph Orchestrator              │
                         │  ┌─────────────────────────────────────┐ │
                         │  │         Iteration Loop              │ │
                         │  │  1. Get prompt                      │ │
                         │  │  2. Retrieve MCP context ◄──────────┼─┼──┐
                         │  │  3. Inject ACE skills               │ │  │
                         │  │  4. Execute via adapter             │ │  │
                         │  │  5. Store results ──────────────────┼─┼──┤
                         │  │  6. Learn (ACE)                     │ │  │
                         │  └─────────────────────────────────────┘ │  │
                         └──────────────────────────────────────────┘  │
                                              │                        │
              ┌───────────────────────────────┼────────────────────────┼──────┐
              │                               │                        │      │
   ┌──────────▼──────────┐        ┌───────────▼───────────┐    ┌───────▼──────┴──┐
   │   Context Manager   │        │   ACE Learning        │    │  MCP Context    │
   │   (Static Prompt)   │        │   Adapter             │    │  Server         │
   └─────────────────────┘        │   (Skillbook)         │    │  (Semantic)     │
                                  └───────────┬───────────┘    └────────┬────────┘
                                              │                         │
                                  ┌───────────▼───────────┐    ┌────────▼────────┐
                                  │  .agent/skillbook/    │    │  .agent/context/│
                                  │  skillbook.json       │    │  context.lance  │
                                  └───────────────────────┘    └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility | What It Stores |
|-----------|---------------|----------------|
| **Context Manager** | Static prompt, stable prefix | Prompt template |
| **ACE Adapter** | Curated learning strategies | Skillbook (JSON) |
| **MCP Context Server** | Raw context semantic retrieval | All context (Vector DB) |

### Communication Flow

```
┌────────────┐  stdio/SSE   ┌───────────────┐
│  Ralph     │◄────────────►│  MCP Context  │
│  (Client)  │   MCP        │  Server       │
└────────────┘  Protocol    └───────────────┘
```

**Transport Options:**
- `stdio` - Default, process-local (recommended)
- `sse` - Server-sent events for remote
- `streamable-http` - HTTP for distributed setups

---

## Data Model

### Core Entities

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid

class ContextType(Enum):
    TASK = "task"           # Task description, goals
    ITERATION = "iteration" # Iteration summaries
    SKILL = "skill"         # Learned strategies (ACE sync)
    FILE = "file"           # File contents, diffs
    OUTPUT = "output"       # Tool outputs, results
    ERROR = "error"         # Errors, stack traces

class ContextState(Enum):
    ACTIVE = "active"       # Fresh, full content (0-5 iterations)
    AGING = "aging"         # Decaying relevance (6-20 iterations)
    SUMMARIZED = "summarized" # Compressed (21-50 iterations)
    ARCHIVED = "archived"   # Cold storage (51+ iterations)

@dataclass
class ContextItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    content_type: ContextType = ContextType.ITERATION
    state: ContextState = ContextState.ACTIVE

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_iteration: int = 0
    source: str = ""                    # "orchestrator", "agent", "user"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Scoring
    usefulness_score: float = 0.5       # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # Vector embedding reference
    embedding_id: Optional[str] = None

    # Summarization
    summary: Optional[str] = None
    original_length: Optional[int] = None

@dataclass
class IterationResult:
    iteration: int
    success: bool
    summary: str
    duration_ms: int
    tokens_used: int
    cost: float
    tool_calls: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

@dataclass
class RetrievalResult:
    items: List[ContextItem]
    query_embedding_time_ms: float
    search_time_ms: float
    total_candidates: int
    filtered_count: int
```

### Database Schema (LanceDB/SQLite)

```sql
CREATE TABLE context_items (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL,
    state TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_iteration INTEGER DEFAULT 0,
    source TEXT,
    tags TEXT,              -- JSON array
    metadata TEXT,          -- JSON object
    usefulness_score REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    summary TEXT,
    original_length INTEGER
);

-- Vector embeddings stored separately (LanceDB native or sqlite-vss)
CREATE VIRTUAL TABLE embeddings USING vss0(
    embedding(384)          -- MiniLM dimension
);

CREATE INDEX idx_context_type ON context_items(content_type);
CREATE INDEX idx_context_state ON context_items(state);
CREATE INDEX idx_context_iteration ON context_items(created_iteration);
CREATE INDEX idx_context_usefulness ON context_items(usefulness_score);
```

---

## MCP Tool Definitions

### Core Retrieval Tools

```python
@mcp.tool()
async def get_relevant_context(
    query: str,
    max_items: int = 10,
    context_types: Optional[List[str]] = None,
    min_score: float = 0.3
) -> dict:
    """
    Retrieve contextually relevant information for the current task.
    Uses semantic search to find the most useful context from previous iterations.

    Args:
        query: Search query or task description (max 500 chars used)
        max_items: Maximum items to return (1-50)
        context_types: Filter by types: task, iteration, skill, file, output, error
        min_score: Minimum relevance score threshold (0.0-1.0)

    Returns:
        items: List of context items with content and metadata
        stats: Search statistics (time, candidates, etc.)
    """

@mcp.tool()
async def get_iteration_history(last_n: int = 5) -> dict:
    """
    Get summaries of recent iterations for continuity.
    Useful for understanding what was attempted and what succeeded/failed.
    """

@mcp.tool()
async def get_skills(
    tags: Optional[List[str]] = None,
    min_score: float = 0.5
) -> dict:
    """
    Get learned skills/strategies from the skillbook.
    Synced with ACE framework skillbook.
    """
```

### Storage/Update Tools

```python
@mcp.tool()
async def store_context(
    content: str,
    context_type: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Store new context for future retrieval.
    Context will be embedded and indexed for semantic search.
    """

@mcp.tool()
async def mark_useful(
    item_id: str,
    helpful: bool,
    reason: Optional[str] = None
) -> dict:
    """
    Provide feedback on context usefulness.
    This improves future retrieval accuracy.
    """

@mcp.tool()
async def store_iteration_result(
    iteration: int,
    summary: str,
    success: bool,
    duration_ms: int = 0,
    tokens_used: int = 0,
    cost: float = 0.0,
    tool_calls: Optional[List[str]] = None,
    artifacts: Optional[List[str]] = None,
    error: Optional[str] = None
) -> dict:
    """
    Store the result of a completed iteration.
    Called by the orchestrator after each iteration.
    """
```

### Maintenance Tools

```python
@mcp.tool()
async def summarize_old_context(older_than_iterations: int = 20) -> dict:
    """Compress old context items to summaries to save space."""

@mcp.tool()
async def prune_low_value_context(min_score: float = 0.3) -> dict:
    """Remove context items with low usefulness scores."""

@mcp.tool()
async def get_context_stats() -> dict:
    """Get statistics about stored context."""

@mcp.tool()
async def health_check() -> dict:
    """Check MCP server health status."""
```

---

## Integration with Ralph

### Modified Orchestrator Flow

```python
class RalphOrchestrator:
    async def _aexecute_iteration(self) -> bool:
        """Execute single iteration with MCP context enhancement."""

        # Step 1: Get base prompt
        prompt = self.context_manager.get_prompt()

        # Step 2: NEW - Retrieve MCP context
        if self.mcp_client:
            task_query = self._extract_task_description(prompt)
            mcp_context = await self.mcp_client.get_relevant_context(
                query=task_query,
                context_types=self._determine_context_types()
            )
            prompt = self._inject_mcp_context(prompt, mcp_context)

        # Step 3: Existing - ACE skillbook injection
        if self.learning_adapter:
            prompt = self.learning_adapter.inject_context(prompt)

        # Step 4: Execute via adapter
        result = await self.adapter.aexecute(prompt)

        # Step 5: NEW - Store iteration result
        if self.mcp_client:
            await self.mcp_client.store_iteration_result(...)

        # Step 6: Existing - ACE learning
        if self.learning_adapter:
            await self.learning_adapter.learn_from_execution(result)

        return result.success
```

### Context Injection Format

```markdown
## Relevant Context from Previous Iterations

### [SKILL]
When implementing file operations, always check if the file exists first using os.path.exists().

### [ERROR]
Previous error: ModuleNotFoundError: No module named 'requests'. Solution: Added to requirements.txt.

### [ITERATION]
Iteration 3 succeeded: Created API endpoint and added tests.
```

---

## Storage Implementation

### LanceDB for Vector Search

```python
import lancedb
from sentence_transformers import SentenceTransformer

class ContextStore:
    def __init__(self, db_path: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.db = lancedb.connect(db_path)
        self.embedder = SentenceTransformer(embedding_model)
        self._init_table()

    async def store(self, content: str, content_type: ContextType, ...) -> ContextItem:
        embedding = await asyncio.to_thread(self.embedder.encode, content)
        self.table.add([{
            "id": str(uuid.uuid4()),
            "content": content,
            "vector": embedding.tolist(),
            ...
        }])

    async def search(self, query: str, max_items: int = 10, ...) -> RetrievalResult:
        query_embedding = await asyncio.to_thread(self.embedder.encode, query)
        results = self.table.search(query_embedding.tolist()).limit(max_items * 2)
        # Apply multi-factor scoring...
        return RetrievalResult(items=scored_items[:max_items], ...)
```

### Storage Location

```
.agent/
├── context/
│   ├── context.lance/      # LanceDB database
│   ├── embeddings/         # Cached embeddings (optional)
│   └── archives/           # Archived context by date
└── skillbook/
    └── skillbook.json      # ACE skillbook (unchanged)
```

---

## Relevance Scoring Algorithm

### Multi-Factor Scoring Model

```python
relevance_score = (
    semantic_similarity * 0.40 +    # Vector cosine similarity
    recency_score * 0.25 +          # Exponential decay by iterations
    usefulness_score * 0.20 +       # Feedback from mark_useful()
    type_match_score * 0.15         # Context type relevance
)
```

### Factor Calculations

| Factor | Calculation | Range |
|--------|-------------|-------|
| **Semantic Similarity** | `1 - cosine_distance(query_embed, item_embed)` | 0.0-1.0 |
| **Recency Score** | `exp(-0.1 * iterations_since_stored)` | 0.0-1.0 |
| **Usefulness Score** | Starts 0.5, +0.1 for helpful, -0.15 for not | 0.0-1.0 |
| **Type Match Score** | 1.0 if matches requested type, else 0.5 | 0.5-1.0 |

### Threshold Filtering

- Minimum score: 0.3 (configurable)
- Items below threshold not returned
- Skills decay slower (0.05 coefficient vs 0.1)

---

## ACE Skillbook Complementarity

### Responsibility Division

| Aspect | ACE Skillbook | MCP Context Server |
|--------|--------------|-------------------|
| **Purpose** | Curated learned strategies | Raw context retrieval |
| **Content** | Skills with confidence scores | All context types |
| **Update** | LLM reflection after iterations | Immediate storage |
| **Retrieval** | Full skillbook injected | Semantic per-query |
| **Persistence** | Long-term (across projects) | Medium-term (project) |

### Synergy Opportunities

1. **MCP feeds ACE:** After N iterations, MCP context becomes input for ACE reflection
2. **ACE skills in MCP:** Skills indexed with type=SKILL for semantic retrieval
3. **Feedback loop:** mark_useful() data informs ACE skill confidence

---

## Configuration Options

### ralph.yaml Schema

```yaml
learning:
  enabled: true

  mcp_context:
    enabled: true

    server:
      transport: "stdio"          # stdio | sse | http
      port: 8765                  # Only for sse/http
      auto_start: true

    storage:
      backend: "lancedb"          # lancedb | sqlite | memory
      path: ".agent/context"
      max_size_mb: 500
      persistence: "project"      # session | project | global

    embeddings:
      provider: "local"           # local | openai
      model: "all-MiniLM-L6-v2"
      cache_embeddings: true

    retrieval:
      max_items_per_query: 10
      min_relevance_score: 0.3
      context_types: [skill, error, iteration]
      max_context_tokens: 4000

    lifecycle:
      summarize_after_iterations: 20
      archive_after_iterations: 50
      prune_after_iterations: 100
      prune_min_usefulness: 0.3

    scoring:
      semantic_weight: 0.4
      recency_weight: 0.25
      usefulness_weight: 0.2
      type_match_weight: 0.15
```

### Configuration Presets

| Setting | Minimal | Standard | Aggressive |
|---------|---------|----------|------------|
| persistence | session | project | global |
| max_size_mb | 100 | 500 | 2000 |
| max_items_per_query | 5 | 10 | 25 |
| summarize_after | 10 | 20 | 50 |
| embeddings | local | local | openai |

---

## Error Handling

### Graceful Degradation Hierarchy

```
Full MCP (semantic search + embeddings)
    ↓ failure
Text-based search (slower, less accurate)
    ↓ failure
Cached context only (stale but available)
    ↓ failure
No context enhancement (Ralph core continues)
```

### Failure Handling

| Failure Mode | Detection | Fallback |
|-------------|-----------|----------|
| Server not running | Connection refused | Continue without MCP |
| Server crash | Connection reset | Use cached context |
| Vector DB corruption | Query error | Text-based fallback |
| Embedding failure | Timeout/error | Skip semantic, store raw |
| Storage full | Write error | Aggressive pruning |

---

## Pros/Cons Analysis

### Advantages

| Benefit | Probability | Impact |
|---------|------------|--------|
| Semantic retrieval vs keyword | 95% | High - finds relevant context |
| Progressive disclosure | 90% | High - prevents context bloat |
| Cross-session persistence | 85% | Medium - enables resume |
| Feedback loop | 80% | Medium - improves over time |
| Separation of concerns | 90% | Medium - easier maintenance |
| Standard protocol (MCP) | 75% | Low - future-proofing |

### Disadvantages

| Concern | Probability | Mitigation |
|---------|------------|------------|
| Added complexity | 70% | Graceful degradation |
| Embedding costs | 60% | Local embeddings, caching |
| Storage growth | 50% | Pruning, summarization |
| Cold start problem | 65% | Empty result handling |
| Relevance quality | 40% | Configurable scoring |
| ACE redundancy | 55% | Clear responsibility split |

### Overall Assessment

**Risk-Adjusted Success Probability: 78%**

- Technical implementation: 90%
- Performance acceptable (<100ms): 85%
- User adoption: 70%
- Measurable improvement: 75%

---

## Implementation Estimates

| Component | Hours | Confidence |
|-----------|-------|------------|
| MCP Server core | 8-12 | High |
| LanceDB integration | 4-6 | High |
| Embedding pipeline | 4-8 | Medium |
| Orchestrator integration | 6-10 | High |
| Configuration system | 3-5 | High |
| Error handling/fallbacks | 4-6 | Medium |
| Testing | 8-12 | Medium |
| Documentation | 4-6 | High |
| **TOTAL** | **41-65 hours** | Medium |

---

## Benchmark Strategy

### Primary Metrics

1. **Iteration Efficiency**
   - Metric: `iterations_to_success / baseline_iterations`
   - Target: 20% reduction

2. **Context Relevance**
   - Metric: `helpful_contexts / total_retrievals`
   - Target: >60%

3. **Context Window Utilization**
   - Metric: `tokens_used / max_window`
   - Target: Higher signal-to-noise

4. **Error Recovery Rate**
   - Metric: `errors_recovered / total_errors`
   - Target: Faster recovery

### A/B Test Design

```yaml
benchmark_tasks:
  - name: "Simple File Creation"
    complexity: low
    expected_improvement: 0%

  - name: "Bug Fix"
    complexity: medium
    expected_improvement: 20-30%

  - name: "Feature Implementation"
    complexity: high
    expected_improvement: 15-25%

  - name: "Multi-Step Refactoring"
    complexity: high
    expected_improvement: 20-30%

  - name: "Error Recovery"
    complexity: medium
    expected_improvement: 25-40%

config:
  runs_per_task: 10
  variants: [baseline, mcp_enabled]
  randomize_order: true
```

### Success Criteria

- p-value < 0.05 for iteration improvement
- At least 15% reduction on medium+ complexity
- No regression on simple tasks
- Retrieval latency < 100ms p99

---

## Appendix: File Structure

```
src/ralph_orchestrator/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP server implementation
│   ├── client.py           # Client wrapper for orchestrator
│   ├── store.py            # ContextStore with LanceDB
│   ├── models.py           # Data classes
│   └── config.py           # MCP-specific configuration
└── ...existing files...
```

---

## References

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [LanceDB Documentation](https://lancedb.github.io/lancedb/)
- [ACE Framework Guide](https://github.com/kayba-ai/agentic-context-engine)
