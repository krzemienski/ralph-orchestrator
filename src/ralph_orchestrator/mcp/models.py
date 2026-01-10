"""
Data models for MCP Context Server.

Defines the core entities used for context storage and retrieval.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class ContextType(Enum):
    """Types of context that can be stored and retrieved."""

    TASK = "task"  # Task description, goals
    ITERATION = "iteration"  # Iteration summaries
    SKILL = "skill"  # Learned strategies (ACE sync)
    FILE = "file"  # File contents, diffs
    OUTPUT = "output"  # Tool outputs, results
    ERROR = "error"  # Errors, stack traces


class ContextState(Enum):
    """Lifecycle states for context items."""

    ACTIVE = "active"  # Fresh, full content (0-5 iterations)
    AGING = "aging"  # Decaying relevance (6-20 iterations)
    SUMMARIZED = "summarized"  # Compressed (21-50 iterations)
    ARCHIVED = "archived"  # Cold storage (51+ iterations)


@dataclass
class ContextItem:
    """A single context item stored in the MCP server."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    content_type: ContextType = ContextType.ITERATION
    state: ContextState = ContextState.ACTIVE

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_iteration: int = 0
    source: str = ""  # "orchestrator", "agent", "user"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Scoring
    usefulness_score: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    # Vector embedding reference
    embedding_id: Optional[str] = None

    # Summarization
    summary: Optional[str] = None
    original_length: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "content_type": self.content_type.value,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "created_iteration": self.created_iteration,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
            "usefulness_score": self.usefulness_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextItem":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            content_type=ContextType(data.get("content_type", "iteration")),
            state=ContextState(data.get("state", "active")),
            created_iteration=data.get("created_iteration", 0),
            source=data.get("source", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            usefulness_score=data.get("usefulness_score", 0.5),
            access_count=data.get("access_count", 0),
            summary=data.get("summary"),
        )


@dataclass
class IterationResult:
    """Result of a completed orchestration iteration."""

    iteration: int
    success: bool
    summary: str
    duration_ms: int = 0
    tokens_used: int = 0
    cost: float = 0.0
    tool_calls: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)  # File paths created/modified
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration": self.iteration,
            "success": self.success,
            "summary": self.summary,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "tool_calls": self.tool_calls,
            "artifacts": self.artifacts,
            "error": self.error,
        }


@dataclass
class RetrievalQuery:
    """Query parameters for context retrieval."""

    query: str
    max_items: int = 10
    context_types: Optional[List[ContextType]] = None
    min_score: float = 0.3
    include_archived: bool = False


@dataclass
class RetrievalResult:
    """Result of a context retrieval operation."""

    items: List[ContextItem]
    query_embedding_time_ms: float = 0.0
    search_time_ms: float = 0.0
    total_candidates: int = 0
    filtered_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "stats": {
                "query_embedding_time_ms": self.query_embedding_time_ms,
                "search_time_ms": self.search_time_ms,
                "total_candidates": self.total_candidates,
                "returned": len(self.items),
            },
        }


@dataclass
class ContextStats:
    """Statistics about the context store."""

    total_items: int = 0
    items_by_type: Dict[str, int] = field(default_factory=dict)
    items_by_state: Dict[str, int] = field(default_factory=dict)
    storage_size_bytes: int = 0
    avg_usefulness_score: float = 0.0
    oldest_item_iteration: int = 0
    newest_item_iteration: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_items": self.total_items,
            "items_by_type": self.items_by_type,
            "items_by_state": self.items_by_state,
            "storage_size_bytes": self.storage_size_bytes,
            "avg_usefulness_score": self.avg_usefulness_score,
            "oldest_item_iteration": self.oldest_item_iteration,
            "newest_item_iteration": self.newest_item_iteration,
        }
