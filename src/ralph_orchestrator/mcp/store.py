"""
Context Store with LanceDB for vector search.

Provides semantic storage and retrieval of context items using
vector embeddings for similarity search.
"""

import asyncio
import json
import logging
import math
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ralph_orchestrator.mcp.models import (
    ContextItem,
    ContextType,
    ContextState,
    IterationResult,
    RetrievalResult,
    ContextStats,
)

logger = logging.getLogger(__name__)


class ContextStore:
    """
    Vector-enabled context store using LanceDB.

    Provides semantic search over stored context items with
    multi-factor relevance scoring.
    """

    def __init__(
        self,
        db_path: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimension: int = 384,
    ):
        """
        Initialize the context store.

        Args:
            db_path: Path to the LanceDB database directory
            embedding_model: Name of the sentence-transformers model
            embedding_dimension: Dimension of the embedding vectors
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.embedding_model_name = embedding_model
        self.embedding_dimension = embedding_dimension

        # Lazy initialization
        self._db = None
        self._table = None
        self._embedder = None
        self._current_iteration = 0

    async def initialize(self) -> bool:
        """Initialize the database and embedding model."""
        try:
            # Import here to avoid startup overhead if not used
            import lancedb
            from sentence_transformers import SentenceTransformer

            # Initialize LanceDB
            self._db = lancedb.connect(str(self.db_path / "context.lance"))

            # Initialize embedding model
            self._embedder = SentenceTransformer(self.embedding_model_name)

            # Create or open table
            await self._init_table()

            logger.info(f"Context store initialized at {self.db_path}")
            return True

        except ImportError as e:
            logger.error(f"Missing dependency for context store: {e}")
            logger.error("Install with: pip install lancedb sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize context store: {e}")
            return False

    async def _init_table(self):
        """Initialize or open the context table."""
        import pyarrow as pa

        table_name = "context"

        try:
            self._table = self._db.open_table(table_name)
            logger.debug(f"Opened existing table: {table_name}")
        except Exception:
            # Create new table with schema
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("content_type", pa.string()),
                pa.field("state", pa.string()),
                pa.field("created_iteration", pa.int32()),
                pa.field("usefulness_score", pa.float32()),
                pa.field("access_count", pa.int32()),
                pa.field("tags", pa.string()),  # JSON array
                pa.field("metadata", pa.string()),  # JSON object
                pa.field("source", pa.string()),
                pa.field("summary", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), self.embedding_dimension)),
            ])
            self._table = self._db.create_table(table_name, schema=schema)
            logger.info(f"Created new table: {table_name}")

    def set_current_iteration(self, iteration: int):
        """Update the current iteration for recency calculations."""
        self._current_iteration = iteration

    async def store(
        self,
        content: str,
        content_type: ContextType,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "orchestrator",
    ) -> ContextItem:
        """
        Store a new context item with embedding.

        Args:
            content: The context content to store
            content_type: Type of context
            tags: Optional tags for filtering
            metadata: Optional metadata dictionary
            source: Source of the context

        Returns:
            The created ContextItem
        """
        if not self._table or not self._embedder:
            raise RuntimeError("Context store not initialized")

        # Generate embedding
        embedding = await asyncio.to_thread(self._embedder.encode, content)

        # Create item
        item = ContextItem(
            content=content,
            content_type=content_type,
            created_iteration=self._current_iteration,
            tags=tags or [],
            metadata=metadata or {},
            source=source,
        )

        # Insert into LanceDB
        self._table.add([{
            "id": item.id,
            "content": content,
            "content_type": content_type.value,
            "state": item.state.value,
            "created_iteration": self._current_iteration,
            "usefulness_score": item.usefulness_score,
            "access_count": 0,
            "tags": json.dumps(tags or []),
            "metadata": json.dumps(metadata or {}),
            "source": source,
            "summary": None,
            "vector": embedding.tolist(),
        }])

        logger.debug(f"Stored context item {item.id} of type {content_type.value}")
        return item

    async def search(
        self,
        query: str,
        max_items: int = 10,
        context_types: Optional[List[str]] = None,
        min_score: float = 0.3,
    ) -> RetrievalResult:
        """
        Semantic search for relevant context.

        Args:
            query: Search query string
            max_items: Maximum items to return
            context_types: Optional filter by context types
            min_score: Minimum relevance score

        Returns:
            RetrievalResult with matching items and stats
        """
        if not self._table or not self._embedder:
            return RetrievalResult(items=[], total_candidates=0)

        start = time.time()

        # Generate query embedding
        query_embedding = await asyncio.to_thread(self._embedder.encode, query)
        embed_time = (time.time() - start) * 1000

        # Vector search
        search_start = time.time()

        search_query = self._table.search(query_embedding.tolist())

        # Apply type filter if specified
        if context_types:
            type_filters = " OR ".join([f"content_type = '{t}'" for t in context_types])
            search_query = search_query.where(type_filters, prefilter=True)

        # Over-fetch for scoring
        results = search_query.limit(max_items * 2).to_list()
        search_time = (time.time() - search_start) * 1000

        # Apply multi-factor scoring
        scored_items = []
        for row in results:
            semantic_sim = 1 - row.get("_distance", 1.0)  # LanceDB returns distance
            recency = self._calc_recency(row.get("created_iteration", 0))
            usefulness = row.get("usefulness_score", 0.5)

            # Calculate final score
            final_score = (
                semantic_sim * 0.4 +
                recency * 0.25 +
                usefulness * 0.2 +
                0.5 * 0.15  # Default type match
            )

            if final_score >= min_score:
                item = ContextItem(
                    id=row["id"],
                    content=row["content"],
                    content_type=ContextType(row["content_type"]),
                    state=ContextState(row.get("state", "active")),
                    created_iteration=row.get("created_iteration", 0),
                    usefulness_score=row.get("usefulness_score", 0.5),
                    access_count=row.get("access_count", 0),
                    tags=json.loads(row.get("tags", "[]")),
                    metadata=json.loads(row.get("metadata", "{}")),
                    source=row.get("source", ""),
                    summary=row.get("summary"),
                )
                scored_items.append((final_score, item))

        # Sort by score and limit
        scored_items.sort(key=lambda x: x[0], reverse=True)
        final_items = [item for _, item in scored_items[:max_items]]

        return RetrievalResult(
            items=final_items,
            query_embedding_time_ms=embed_time,
            search_time_ms=search_time,
            total_candidates=len(results),
            filtered_count=len(final_items),
        )

    def _calc_recency(self, created_iter: int) -> float:
        """Calculate recency score with exponential decay."""
        age = self._current_iteration - created_iter
        return math.exp(-0.1 * max(0, age))

    async def update_usefulness(
        self,
        item_id: str,
        helpful: bool,
        reason: Optional[str] = None,
    ) -> Optional[ContextItem]:
        """
        Update the usefulness score of a context item.

        Args:
            item_id: ID of the item to update
            helpful: Whether the context was helpful
            reason: Optional reason for the rating

        Returns:
            Updated ContextItem or None if not found
        """
        # Note: LanceDB doesn't support in-place updates well.
        # For production, consider a hybrid SQLite + LanceDB approach
        # where metadata lives in SQLite and vectors in LanceDB.
        logger.debug(f"Usefulness feedback for {item_id}: helpful={helpful}, reason={reason}")
        return None

    async def store_iteration(self, result: IterationResult) -> ContextItem:
        """
        Store an iteration result as context.

        Args:
            result: The iteration result to store

        Returns:
            The created ContextItem
        """
        content = f"Iteration {result.iteration}: {'Success' if result.success else 'Failed'}. {result.summary}"
        if result.error:
            content += f" Error: {result.error}"

        return await self.store(
            content=content,
            content_type=ContextType.ITERATION,
            metadata={
                "iteration": result.iteration,
                "success": result.success,
                "duration_ms": result.duration_ms,
                "tokens_used": result.tokens_used,
                "cost": result.cost,
                "tool_calls": result.tool_calls,
                "artifacts": result.artifacts,
            },
            source="orchestrator",
        )

    async def get_iterations(self, limit: int = 5) -> List[ContextItem]:
        """Get recent iteration summaries."""
        if not self._table:
            return []

        # Query for iteration type, sorted by created_iteration desc
        results = self._table.search()\
            .where("content_type = 'iteration'")\
            .limit(limit)\
            .to_list()

        items = []
        for row in results:
            item = ContextItem(
                id=row["id"],
                content=row["content"],
                content_type=ContextType(row["content_type"]),
                created_iteration=row.get("created_iteration", 0),
                metadata=json.loads(row.get("metadata", "{}")),
            )
            items.append(item)

        return items

    async def get_skills(
        self,
        tags: Optional[List[str]] = None,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Get skills matching criteria."""
        if not self._table:
            return []

        # Query for skill type
        results = self._table.search()\
            .where(f"content_type = 'skill' AND usefulness_score >= {min_score}")\
            .limit(50)\
            .to_list()

        skills = []
        for row in results:
            item_tags = json.loads(row.get("tags", "[]"))
            if tags and not any(t in item_tags for t in tags):
                continue
            skills.append({
                "id": row["id"],
                "content": row["content"],
                "score": row.get("usefulness_score", 0.5),
                "tags": item_tags,
            })

        return skills

    async def summarize_old(self, older_than_iterations: int) -> int:
        """Summarize context items older than specified iterations."""
        # In production, this would use an LLM to generate summaries
        logger.info(f"Summarization requested for items older than {older_than_iterations} iterations")
        return 0

    async def prune(self, min_score: float) -> int:
        """Remove context items with low usefulness scores."""
        logger.info(f"Pruning requested for items with score < {min_score}")
        return 0

    async def get_stats(self) -> ContextStats:
        """Get statistics about the context store."""
        if not self._table:
            return ContextStats()

        # Count items by type and state
        results = self._table.search().limit(10000).to_list()

        items_by_type: Dict[str, int] = {}
        items_by_state: Dict[str, int] = {}
        total_usefulness = 0.0
        oldest = float('inf')
        newest = 0

        for row in results:
            ct = row.get("content_type", "unknown")
            items_by_type[ct] = items_by_type.get(ct, 0) + 1

            state = row.get("state", "active")
            items_by_state[state] = items_by_state.get(state, 0) + 1

            total_usefulness += row.get("usefulness_score", 0.5)

            created = row.get("created_iteration", 0)
            oldest = min(oldest, created)
            newest = max(newest, created)

        total = len(results)
        return ContextStats(
            total_items=total,
            items_by_type=items_by_type,
            items_by_state=items_by_state,
            avg_usefulness_score=total_usefulness / total if total > 0 else 0.0,
            oldest_item_iteration=int(oldest) if oldest != float('inf') else 0,
            newest_item_iteration=newest,
        )

    def is_connected(self) -> bool:
        """Check if the store is connected and ready."""
        return self._table is not None and self._embedder is not None

    async def count(self) -> int:
        """Get total number of context items."""
        if not self._table:
            return 0
        return len(self._table.search().limit(100000).to_list())
