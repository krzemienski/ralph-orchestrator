# Approach #2: LangChain/LangGraph Memory Integration for Ralph

**Author:** Opus 4.5 Architect
**Date:** 2026-01-10
**Status:** Design Complete

---

## Executive Summary

This document presents a design for integrating LangChain/LangGraph memory patterns into Ralph Orchestrator to optimize context management. After analyzing both full framework adoption and pattern extraction approaches, **we recommend extracting LangGraph's key patterns without adopting the full framework**.

The core innovation is replacing Ralph's current "inject ALL skills" approach with **semantic memory search** that injects only the TOP-K most relevant skills based on the current task.

---

## 1. Research Findings

### 1.1 LangGraph Memory Architecture

LangGraph separates memory into two distinct layers:

| Layer | Scope | Purpose | LangGraph Implementation |
|-------|-------|---------|--------------------------|
| **Short-term** | Thread/Session | Execution state, conversation history | Checkpointers (MemorySaver, PostgresSaver) |
| **Long-term** | Cross-session | Persistent knowledge, learned facts | Stores (InMemoryStore, PostgresStore) |

Key patterns discovered:
1. **Namespace Organization**: `(user_id, memory_type)` tuples for hierarchical memory
2. **Semantic Search**: Embedding-based retrieval with `store.search(namespace, query, limit)`
3. **Multi-field Embedding**: Index multiple fields like `["memory", "emotional_context"]`
4. **Procedural Memory**: Agents can update their own instructions (system prompts)

### 1.2 Ralph's Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Current Ralph Memory                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │    ContextManager       │  │   ACELearningAdapter     │  │
│  │                         │  │                          │  │
│  │  - stable_prefix        │  │  - skillbook (JSON)      │  │
│  │  - dynamic_context[5]   │  │  - reflector             │  │
│  │  - error_history[5]     │  │  - skill_manager         │  │
│  │  - success_patterns[3]  │  │  - inject_context()      │  │
│  └─────────────────────────┘  └──────────────────────────┘  │
│              │                           │                   │
│              └───────────┬───────────────┘                   │
│                          ▼                                   │
│              ┌─────────────────────────┐                     │
│              │   Prompt Enhancement    │                     │
│              │   (inject ALL skills)   │  <-- PROBLEM        │
│              └─────────────────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Current Problem**: `inject_context()` adds ALL skills from the skillbook, regardless of relevance to the current task. This:
- Wastes tokens on irrelevant skills
- Doesn't scale as skillbook grows
- Provides no task-awareness

---

## 2. Framework Integration Decision

### 2.1 Option A: Full LangGraph Adoption

**Pros:**
- Production-tested InMemoryStore with semantic search
- Robust async checkpointers (PostgresSaver, SqliteSaver)
- Active development and community

**Cons:**
- Heavy dependency (~100MB+, pulls LangChain core)
- Pydantic v1/v2 conflicts (already seen with ACE)
- Ralph's loop-based model doesn't fit LangGraph's graph paradigm
- Overkill for Ralph's simple iteration pattern

### 2.2 Option B: Pattern Extraction (RECOMMENDED)

**Pros:**
- Minimal dependencies (numpy for similarity)
- Uses existing LiteLLMClient for embeddings
- Matches Ralph's lightweight philosophy
- Full control over implementation

**Cons:**
- More implementation effort
- No community support for our implementation

### 2.3 Decision: Option B - Pattern Extraction

We will extract and adapt LangGraph's patterns without adopting the framework:
1. Build `RalphMemoryStore` inspired by `InMemoryStore`
2. Use existing `LiteLLMClient` for embeddings
3. JSON file persistence (matches skillbook approach)
4. Integrate with existing ACE learning adapter

---

## 3. Architectural Design

### 3.1 Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ralph Memory Architecture v2                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    RalphMemoryBridge                        │ │
│  │  - Routes queries to appropriate store                      │ │
│  │  - Combines short-term + long-term results                  │ │
│  │  - Manages embedding generation                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│           │                              │                       │
│           ▼                              ▼                       │
│  ┌─────────────────────┐    ┌─────────────────────────┐         │
│  │  ShortTermStore     │    │    LongTermStore         │         │
│  │  (In-Memory)        │    │    (File-Backed)         │         │
│  │                     │    │                          │         │
│  │  - Session context  │    │  - ACE Skillbook         │         │
│  │  - Recent errors    │    │  - Cross-session skills  │         │
│  │  - Current task     │    │  - Error patterns        │         │
│  │  - Iteration state  │    │  - Success patterns      │         │
│  │  - TTL: session     │    │  - TTL: persistent       │         │
│  └─────────────────────┘    └─────────────────────────┘         │
│           │                              │                       │
│           └──────────────┬───────────────┘                       │
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    SemanticInjector                         │ │
│  │  - Query both stores with current task                      │ │
│  │  - Rank by cosine similarity                                │ │
│  │  - Inject TOP-K into prompt                                 │ │
│  │  - Format with relevance scores                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│                          ▼                                       │
│              ┌─────────────────────────┐                         │
│              │   Enhanced Prompt       │                         │
│              │   (TOP-5 relevant       │                         │
│              │    skills only)         │                         │
│              └─────────────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Namespace Design

Inspired by LangGraph's `(user_id, memory_type)` pattern:

```python
NAMESPACE_HIERARCHY = {
    # Project-scoped skills (learned from this project)
    ("project", "{project_name}", "skills"): "Project-specific strategies",

    # Global skills (transferable across projects)
    ("global", "skills"): "Universal agent patterns",

    # Error patterns (helps avoid repeating mistakes)
    ("project", "{project_name}", "errors"): "Failed approaches to avoid",

    # Success patterns (helps replicate wins)
    ("project", "{project_name}", "successes"): "Proven successful approaches",

    # Context snapshots (for time-travel debugging)
    ("project", "{project_name}", "snapshots", "{iteration}"): "Point-in-time state",
}
```

### 3.3 Data Flow

```
Iteration Start
      │
      ▼
┌─────────────────────────┐
│ Extract current task    │
│ from prompt/task_queue  │
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│ Generate task embedding │
│ (via LiteLLMClient)     │
└─────────────────────────┘
      │
      ├──────────────────────────────┐
      ▼                              ▼
┌─────────────────┐        ┌─────────────────┐
│ Search short-   │        │ Search long-    │
│ term store      │        │ term store      │
│ (session ctx)   │        │ (skills)        │
└─────────────────┘        └─────────────────┘
      │                              │
      └──────────────┬───────────────┘
                     ▼
          ┌─────────────────────┐
          │ Merge & rank by     │
          │ cosine similarity   │
          └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Take TOP-K (5-10)   │
          │ most relevant       │
          └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Format and inject   │
          │ into prompt         │
          └─────────────────────┘
                     │
                     ▼
              Execute Iteration
                     │
                     ▼
┌─────────────────────────────────┐
│ After iteration:                │
│ - Update short-term with output │
│ - ACE learning updates skills   │
│ - Skills stored with embeddings │
└─────────────────────────────────┘
```

---

## 4. Sample Implementation

### 4.1 RalphMemoryStore Class

```python
# src/ralph_orchestrator/memory/store.py
"""
Semantic memory store inspired by LangGraph's InMemoryStore.
Provides namespace-organized storage with embedding-based search.
"""

import json
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging

logger = logging.getLogger('ralph-orchestrator.memory')


@dataclass
class MemoryItem:
    """A single memory item with metadata and optional embedding."""
    key: str
    value: Dict[str, Any]
    namespace: Tuple[str, ...]
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    score: float = 0.0  # Relevance score from search

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'value': self.value,
            'namespace': list(self.namespace),
            'embedding': self.embedding,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        return cls(
            key=data['key'],
            value=data['value'],
            namespace=tuple(data['namespace']),
            embedding=data.get('embedding'),
            created_at=data.get('created_at', datetime.utcnow().isoformat() + 'Z'),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat() + 'Z'),
        )


class EmbeddingProvider:
    """Abstract embedding generation using LiteLLM or local models."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dims: int = 1536,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.dims = dims
        self.api_key = api_key
        self._cache: Dict[str, List[float]] = {}

    def embed(self, text: str) -> List[float]:
        """Generate embedding for text, with caching."""
        cache_key = hashlib.sha256(text.encode()).hexdigest()[:16]

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            import litellm
            response = litellm.embedding(
                model=self.model,
                input=[text],
                api_key=self.api_key,
            )
            embedding = response.data[0]['embedding']
            self._cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            # Return zero vector as fallback
            return [0.0] * self.dims

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]


class RalphMemoryStore:
    """
    Semantic memory store with namespace organization and embedding search.

    Inspired by LangGraph's InMemoryStore but adapted for Ralph's needs:
    - JSON file persistence (matches skillbook approach)
    - Uses LiteLLM for embeddings
    - Thread-safe operations

    Example:
        store = RalphMemoryStore(
            persist_path=".agent/memory/store.json",
            embedding_model="text-embedding-3-small",
        )

        # Store a skill
        store.put(
            namespace=("project", "my-app", "skills"),
            key="error-handling-01",
            value={"strategy": "Always validate inputs before processing"},
        )

        # Search for relevant skills
        results = store.search(
            namespace=("project", "my-app", "skills"),
            query="How to handle user input errors?",
            limit=5,
        )
    """

    def __init__(
        self,
        persist_path: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        embedding_dims: int = 1536,
        embedding_fields: List[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize memory store.

        Args:
            persist_path: Path to JSON file for persistence. None for in-memory only.
            embedding_model: Model for embedding generation.
            embedding_dims: Dimensions of embeddings.
            embedding_fields: Fields to embed from value dict. Default: ["$"] (entire value)
            api_key: API key for embedding provider.
        """
        self.persist_path = Path(persist_path) if persist_path else None
        self.embedding_fields = embedding_fields or ["$"]
        self._lock = threading.Lock()
        self._store: Dict[Tuple[str, ...], Dict[str, MemoryItem]] = {}

        # Initialize embedding provider
        self._embedder = EmbeddingProvider(
            model=embedding_model,
            dims=embedding_dims,
            api_key=api_key,
        )

        # Load existing data
        if self.persist_path and self.persist_path.exists():
            self._load()

    def put(
        self,
        namespace: Tuple[str, ...],
        key: str,
        value: Dict[str, Any],
        index: bool = True,
    ) -> None:
        """
        Store a memory item.

        Args:
            namespace: Tuple of strings forming hierarchical namespace.
            key: Unique key within namespace.
            value: Dictionary of data to store.
            index: Whether to generate embedding for search. Set False for metadata.
        """
        with self._lock:
            if namespace not in self._store:
                self._store[namespace] = {}

            # Generate embedding if indexing enabled
            embedding = None
            if index:
                text_to_embed = self._extract_text_for_embedding(value)
                if text_to_embed:
                    embedding = self._embedder.embed(text_to_embed)

            # Check if updating existing item
            if key in self._store[namespace]:
                existing = self._store[namespace][key]
                item = MemoryItem(
                    key=key,
                    value=value,
                    namespace=namespace,
                    embedding=embedding,
                    created_at=existing.created_at,
                    updated_at=datetime.utcnow().isoformat() + 'Z',
                )
            else:
                item = MemoryItem(
                    key=key,
                    value=value,
                    namespace=namespace,
                    embedding=embedding,
                )

            self._store[namespace][key] = item

            # Persist if path configured
            if self.persist_path:
                self._save()

    def get(
        self,
        namespace: Tuple[str, ...],
        key: str,
    ) -> Optional[MemoryItem]:
        """Retrieve a specific memory item by namespace and key."""
        with self._lock:
            if namespace in self._store:
                return self._store[namespace].get(key)
            return None

    def search(
        self,
        namespace: Tuple[str, ...],
        query: str,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> List[MemoryItem]:
        """
        Search for relevant memories using semantic similarity.

        Args:
            namespace: Namespace to search within.
            query: Natural language search query.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score (0-1) to include.

        Returns:
            List of MemoryItems sorted by relevance (highest first).
        """
        with self._lock:
            if namespace not in self._store:
                return []

            # Generate query embedding
            query_embedding = self._embedder.embed(query)
            query_vec = np.array(query_embedding)

            results = []
            for item in self._store[namespace].values():
                if item.embedding is None:
                    continue

                # Calculate cosine similarity
                item_vec = np.array(item.embedding)
                similarity = self._cosine_similarity(query_vec, item_vec)

                if similarity >= min_score:
                    # Create copy with score
                    scored_item = MemoryItem(
                        key=item.key,
                        value=item.value,
                        namespace=item.namespace,
                        embedding=item.embedding,
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                        score=similarity,
                    )
                    results.append(scored_item)

            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

    def list(
        self,
        namespace: Tuple[str, ...],
        prefix: Optional[str] = None,
    ) -> List[MemoryItem]:
        """List all items in a namespace, optionally filtered by key prefix."""
        with self._lock:
            if namespace not in self._store:
                return []

            items = list(self._store[namespace].values())
            if prefix:
                items = [i for i in items if i.key.startswith(prefix)]
            return items

    def delete(
        self,
        namespace: Tuple[str, ...],
        key: str,
    ) -> bool:
        """Delete a memory item. Returns True if deleted, False if not found."""
        with self._lock:
            if namespace in self._store and key in self._store[namespace]:
                del self._store[namespace][key]
                if self.persist_path:
                    self._save()
                return True
            return False

    def clear_namespace(self, namespace: Tuple[str, ...]) -> int:
        """Clear all items in a namespace. Returns count of deleted items."""
        with self._lock:
            if namespace in self._store:
                count = len(self._store[namespace])
                del self._store[namespace]
                if self.persist_path:
                    self._save()
                return count
            return 0

    def _extract_text_for_embedding(self, value: Dict[str, Any]) -> str:
        """Extract text from value dict based on embedding_fields config."""
        texts = []
        for field in self.embedding_fields:
            if field == "$":
                # Embed entire value as JSON string
                texts.append(json.dumps(value, sort_keys=True))
            elif field in value:
                texts.append(str(value[field]))
        return " ".join(texts)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _save(self) -> None:
        """Persist store to JSON file."""
        if not self.persist_path:
            return

        self.persist_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        data = {}
        for namespace, items in self._store.items():
            ns_key = "/".join(namespace)
            data[ns_key] = {
                key: item.to_dict()
                for key, item in items.items()
            }

        self.persist_path.write_text(json.dumps(data, indent=2))

    def _load(self) -> None:
        """Load store from JSON file."""
        if not self.persist_path or not self.persist_path.exists():
            return

        try:
            data = json.loads(self.persist_path.read_text())
            for ns_key, items in data.items():
                namespace = tuple(ns_key.split("/"))
                self._store[namespace] = {
                    key: MemoryItem.from_dict(item_data)
                    for key, item_data in items.items()
                }
            logger.info(f"Loaded memory store from {self.persist_path}")
        except Exception as e:
            logger.warning(f"Failed to load memory store: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the store."""
        with self._lock:
            total_items = sum(len(items) for items in self._store.values())
            namespaces = list(self._store.keys())
            return {
                "total_items": total_items,
                "namespace_count": len(namespaces),
                "namespaces": ["/".join(ns) for ns in namespaces],
                "persist_path": str(self.persist_path) if self.persist_path else None,
            }
```

### 4.2 SemanticInjector Class

```python
# src/ralph_orchestrator/memory/injector.py
"""
Semantic context injection for Ralph prompts.
Replaces the current 'inject ALL skills' approach with relevance-based selection.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from .store import RalphMemoryStore, MemoryItem

logger = logging.getLogger('ralph-orchestrator.memory')


@dataclass
class InjectionConfig:
    """Configuration for semantic injection."""
    max_skills: int = 5
    max_short_term: int = 3
    min_relevance_score: float = 0.3
    include_scores: bool = True
    format_template: str = "markdown"  # or "xml", "json"


class SemanticInjector:
    """
    Injects semantically relevant context into prompts.

    Combines results from short-term and long-term memory stores,
    ranks by relevance to current task, and formats for prompt injection.

    Example:
        injector = SemanticInjector(
            short_term_store=session_store,
            long_term_store=persistent_store,
        )

        enhanced_prompt = injector.inject(
            prompt=original_prompt,
            task="Implement error handling for user input validation",
            project="my-app",
        )
    """

    def __init__(
        self,
        short_term_store: Optional[RalphMemoryStore] = None,
        long_term_store: Optional[RalphMemoryStore] = None,
        config: Optional[InjectionConfig] = None,
    ):
        self.short_term = short_term_store
        self.long_term = long_term_store
        self.config = config or InjectionConfig()

    def inject(
        self,
        prompt: str,
        task: str,
        project: str = "default",
        extra_context: Optional[str] = None,
    ) -> str:
        """
        Inject relevant context into prompt.

        Args:
            prompt: Original prompt text.
            task: Current task description for relevance matching.
            project: Project name for namespace scoping.
            extra_context: Additional context to consider in search.

        Returns:
            Enhanced prompt with relevant context injected.
        """
        search_query = task
        if extra_context:
            search_query = f"{task}\n{extra_context}"

        # Collect results from both stores
        all_results: List[MemoryItem] = []

        # Search short-term store (session context)
        if self.short_term:
            short_term_results = self.short_term.search(
                namespace=("session", "context"),
                query=search_query,
                limit=self.config.max_short_term,
                min_score=self.config.min_relevance_score,
            )
            all_results.extend(short_term_results)

        # Search long-term store (skills)
        if self.long_term:
            # Search project-specific skills
            project_skills = self.long_term.search(
                namespace=("project", project, "skills"),
                query=search_query,
                limit=self.config.max_skills,
                min_score=self.config.min_relevance_score,
            )
            all_results.extend(project_skills)

            # Also search global skills
            global_skills = self.long_term.search(
                namespace=("global", "skills"),
                query=search_query,
                limit=self.config.max_skills // 2,
                min_score=self.config.min_relevance_score,
            )
            all_results.extend(global_skills)

        if not all_results:
            logger.debug("No relevant context found for injection")
            return prompt

        # Sort all results by score and take top-K
        all_results.sort(key=lambda x: x.score, reverse=True)
        top_results = all_results[:self.config.max_skills + self.config.max_short_term]

        # Format injection
        injection = self._format_injection(top_results)

        logger.info(
            f"Injected {len(top_results)} relevant items | "
            f"scores: {[f'{r.score:.2f}' for r in top_results[:5]]}"
        )

        return f"{prompt}\n\n{injection}"

    def _format_injection(self, items: List[MemoryItem]) -> str:
        """Format memory items for prompt injection."""
        if self.config.format_template == "markdown":
            return self._format_markdown(items)
        elif self.config.format_template == "xml":
            return self._format_xml(items)
        else:
            return self._format_json(items)

    def _format_markdown(self, items: List[MemoryItem]) -> str:
        """Format as markdown."""
        lines = ["## Relevant Context (Semantic Memory)"]
        lines.append("")
        lines.append("The following strategies and context are relevant to your current task:")
        lines.append("")

        for i, item in enumerate(items, 1):
            score_str = f" (relevance: {item.score:.2f})" if self.config.include_scores else ""
            lines.append(f"### {i}. {item.key}{score_str}")

            # Format value
            value = item.value
            if isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f"- **{k}**: {v}")
            else:
                lines.append(str(value))
            lines.append("")

        return "\n".join(lines)

    def _format_xml(self, items: List[MemoryItem]) -> str:
        """Format as XML."""
        lines = ["<semantic_context>"]

        for item in items:
            score_attr = f' relevance="{item.score:.2f}"' if self.config.include_scores else ""
            lines.append(f'  <memory key="{item.key}"{score_attr}>')

            value = item.value
            if isinstance(value, dict):
                for k, v in value.items():
                    lines.append(f"    <{k}>{v}</{k}>")
            else:
                lines.append(f"    {value}")

            lines.append("  </memory>")

        lines.append("</semantic_context>")
        return "\n".join(lines)

    def _format_json(self, items: List[MemoryItem]) -> str:
        """Format as JSON."""
        import json
        data = [
            {
                "key": item.key,
                "relevance": item.score if self.config.include_scores else None,
                "value": item.value,
            }
            for item in items
        ]
        return f"```json\n{json.dumps(data, indent=2)}\n```"
```

### 4.3 Integration with Orchestrator

```python
# Changes to src/ralph_orchestrator/orchestrator.py

# In __init__, add memory store initialization:
def _initialize_memory_stores(self) -> tuple:
    """Initialize short-term and long-term memory stores."""
    from .memory.store import RalphMemoryStore
    from .memory.injector import SemanticInjector, InjectionConfig

    # Short-term: in-memory only (session-scoped)
    short_term = RalphMemoryStore(
        persist_path=None,  # Not persisted
        embedding_model=getattr(self._config, 'embedding_model', 'text-embedding-3-small'),
    )

    # Long-term: file-backed (cross-session)
    long_term = RalphMemoryStore(
        persist_path=".agent/memory/long_term.json",
        embedding_model=getattr(self._config, 'embedding_model', 'text-embedding-3-small'),
        embedding_fields=["strategy", "content", "description"],
    )

    # Semantic injector
    injector = SemanticInjector(
        short_term_store=short_term,
        long_term_store=long_term,
        config=InjectionConfig(
            max_skills=getattr(self._config, 'memory_max_skills', 5),
            max_short_term=getattr(self._config, 'memory_max_short_term', 3),
            min_relevance_score=getattr(self._config, 'memory_min_score', 0.3),
        ),
    )

    return short_term, long_term, injector


# In _aexecute_iteration, replace inject_context:
async def _aexecute_iteration(self) -> bool:
    """Execute a single iteration asynchronously."""
    prompt = self.context_manager.get_prompt()

    # NEW: Use semantic injection instead of inject_all
    if self.semantic_injector:
        task_description = self.current_task.get('description', '') if self.current_task else ''
        if not task_description:
            # Extract from prompt
            task_description = prompt[:500]

        prompt = self.semantic_injector.inject(
            prompt=prompt,
            task=task_description,
            project=self._get_project_name(),
        )
    elif self.learning_adapter:
        # Fallback to old behavior
        prompt = self.learning_adapter.inject_context(prompt)

    # ... rest of iteration logic ...


# After successful iteration, update stores:
if response.success:
    # Update short-term store with iteration context
    self.short_term_store.put(
        namespace=("session", "context"),
        key=f"iteration-{self.metrics.iterations}",
        value={
            "task": task_context,
            "output_summary": response.output[:500] if response.output else "",
            "success": True,
        },
    )
```

---

## 5. Pros and Cons Analysis

### 5.1 Pros (with Probability Scores)

| Benefit | Probability | Impact | Description |
|---------|-------------|--------|-------------|
| Token Efficiency | 0.95 | High | Semantic search injects only TOP-K relevant skills instead of ALL skills. Expect 40-60% token reduction. |
| Better Task-Skill Matching | 0.85 | High | Skills retrieved based on semantic similarity to current task. Should improve iteration success rate. |
| Scalability | 0.90 | High | Current approach degrades as skillbook grows. Semantic search maintains O(log n) performance with embeddings. |
| No Major Dependencies | 0.95 | Medium | Pattern extraction over framework adoption. Uses existing LiteLLMClient. Matches Ralph's lightweight philosophy. |
| Cross-Project Learning | 0.75 | Medium | Namespace organization enables skill sharing between similar projects. |
| Time-Travel Debugging | 0.80 | Medium | Snapshot memory state at each iteration. Reproduce issues from specific state. |

### 5.2 Cons (with Probability Scores)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Embedding API Costs | 0.90 | Low | ~$0.02/1M tokens adds up over time. Use caching, batch operations, or local embeddings. |
| Latency Overhead | 0.70 | Medium | Embedding generation adds 50-200ms. Use async embedding, pre-compute during idle. |
| Cold Start Problem | 0.85 | Medium | New projects have no skills. Provide "starter" skill sets or fall back to no injection. |
| Complexity Increase | 0.80 | Medium | More moving parts. Document thoroughly, add telemetry for debugging. |
| Similarity Threshold Tuning | 0.75 | Medium | Wrong threshold = bad selection. Start with 0.3, tune based on benchmarks. |
| Embedding Drift | 0.60 | Low | Switching models invalidates embeddings. Store model version, rebuild on change. |
| ACE Integration | 0.65 | Medium | Need to sync with existing skillbook. Use ACE as source, memory store for retrieval. |

---

## 6. Implementation Complexity

### 6.1 Component Breakdown

| Component | Effort (Hours) | Dependencies | Risk |
|-----------|---------------|--------------|------|
| RalphMemoryStore class | 16-24 | numpy | Low |
| EmbeddingProvider class | 8-12 | litellm (existing) | Low |
| SemanticInjector class | 6-8 | RalphMemoryStore | Low |
| ContextManager enhancements | 8-12 | SemanticInjector | Medium |
| ACELearningAdapter integration | 8-12 | RalphMemoryStore | Medium |
| Orchestrator integration | 4-6 | All above | Medium |
| Testing & benchmarks | 12-16 | All above | Low |
| Documentation | 4-6 | - | Low |

**Total Estimate: 66-96 hours (1.5-2.5 weeks full-time)**

### 6.2 Dependency Analysis

**New Dependencies:**
- `numpy` - For cosine similarity (likely already installed via other deps)

**Existing Dependencies Used:**
- `litellm` - Via ACE's LiteLLMClient for embeddings
- `json` - Standard library
- `threading` - Standard library

**Optional Dependencies:**
- `sentence-transformers` - For local embeddings (offline mode)
- `psycopg` - For PostgresStore (production scaling)

---

## 7. Benchmark Strategy

### 7.1 Baseline Metrics

Capture before implementing semantic memory:
- Average iterations to completion
- Token usage per iteration (input + output)
- Success rate (successful / total iterations)
- Time per iteration (wall clock)
- Skillbook size growth rate

### 7.2 Test Scenarios

| Scenario | Expected Iterations | Purpose |
|----------|---------------------|---------|
| Simple task | 1-3 | Baseline validation |
| Medium task | 5-10 | Normal operation |
| Complex task | 15+ | Stress test |
| Repeated similar tasks | N/A | Skill transfer |
| New project cold-start | N/A | Edge case |

### 7.3 A/B Test Design

```
Group A: Current inject_all (control)
Group B: Semantic search TOP-5
Group C: Semantic search TOP-10
Group D: Hybrid (recency + semantic)
```

### 7.4 Success Criteria

| Metric | Target | Priority |
|--------|--------|----------|
| Token reduction | >20% with same/better success rate | P0 |
| Latency increase | <5% per iteration | P0 |
| Skill relevance | >80% rated "relevant" by eval | P1 |
| Iteration reduction | >10% for repeated tasks | P1 |

### 7.5 Comparison with Other Approaches

| Metric | Approach #1 (Context Compression) | Approach #2 (LangGraph Memory) | Approach #3 (TBD) |
|--------|-----------------------------------|--------------------------------|-------------------|
| Token reduction | 30-50% | 40-60% | - |
| Latency impact | +5-10% | +3-5% | - |
| Implementation effort | 40-60h | 60-90h | - |
| New dependencies | tiktoken | numpy | - |
| Skill relevance | N/A (no skills) | >80% | - |

---

## 8. Appendix

### 8.1 LangGraph Memory Patterns Reference

Key patterns extracted from LangGraph documentation:

1. **Namespace-based organization**: `store.put(namespace, key, value)`
2. **Semantic search**: `store.search(namespace, query, limit)`
3. **Multi-field embedding**: `{"fields": ["memory", "context"]}`
4. **Selective indexing**: `store.put(..., index=False)` for metadata
5. **Procedural memory**: Agent updates its own instructions

### 8.2 Related Memory Observations

- Memory #12681: LangGraph short-term vs long-term memory patterns
- Memory #12690: LangGraph InMemoryStore semantic search details

### 8.3 Source References

- [LangChain Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangGraph Persistence Concepts](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/persistence.md)
- [DeepLearning.AI: Long-Term Agentic Memory](https://www.deeplearning.ai/short-courses/long-term-agentic-memory-with-langgraph/)
- [MongoDB LangGraph Integration](https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph)
