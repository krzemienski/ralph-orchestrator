"""
MCP Context Server for Progressive Context Disclosure.

This server provides tools for storing and retrieving context
across Ralph orchestrator iterations using semantic search.
"""

import asyncio
import logging
import os
from typing import Optional, List

from mcp.server.fastmcp import FastMCP

from ralph_orchestrator.mcp.models import ContextType, IterationResult
from ralph_orchestrator.mcp.store import ContextStore

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("ralph-context", json_response=True)

# Global store instance (initialized on startup)
context_store: Optional[ContextStore] = None


async def initialize_store():
    """Initialize the context store on server startup."""
    global context_store

    db_path = os.environ.get("RALPH_CONTEXT_DB_PATH", ".agent/context")
    embedding_model = os.environ.get("RALPH_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    context_store = ContextStore(db_path=db_path, embedding_model=embedding_model)
    success = await context_store.initialize()

    if not success:
        logger.error("Failed to initialize context store")
        raise RuntimeError("Context store initialization failed")

    logger.info("MCP Context Server initialized successfully")


# ============ Core Retrieval Tools ============


@mcp.tool()
async def get_relevant_context(
    query: str,
    max_items: int = 10,
    context_types: Optional[List[str]] = None,
    min_score: float = 0.3,
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
    if not context_store:
        return {"error": "Context store not initialized", "items": []}

    # Validate and clamp parameters
    max_items = max(1, min(50, max_items))
    min_score = max(0.0, min(1.0, min_score))
    query = query[:500]  # Truncate long queries

    result = await context_store.search(
        query=query,
        max_items=max_items,
        context_types=context_types,
        min_score=min_score,
    )

    return result.to_dict()


@mcp.tool()
async def get_iteration_history(last_n: int = 5) -> dict:
    """
    Get summaries of recent iterations for continuity.
    Useful for understanding what was attempted and what succeeded/failed.

    Args:
        last_n: Number of recent iterations to retrieve (1-20)

    Returns:
        iterations: List of iteration summaries
        count: Number of iterations returned
    """
    if not context_store:
        return {"error": "Context store not initialized", "iterations": [], "count": 0}

    last_n = max(1, min(20, last_n))
    iterations = await context_store.get_iterations(limit=last_n)

    return {
        "iterations": [it.to_dict() for it in iterations],
        "count": len(iterations),
    }


@mcp.tool()
async def get_skills(
    tags: Optional[List[str]] = None,
    min_score: float = 0.5,
) -> dict:
    """
    Get learned skills/strategies from the context store.
    Skills are strategies that have been proven useful across iterations.

    Args:
        tags: Optional list of tags to filter by
        min_score: Minimum usefulness score (0.0-1.0)

    Returns:
        skills: List of skills with content and scores
        count: Number of skills returned
    """
    if not context_store:
        return {"error": "Context store not initialized", "skills": [], "count": 0}

    min_score = max(0.0, min(1.0, min_score))
    skills = await context_store.get_skills(tags=tags, min_score=min_score)

    return {"skills": skills, "count": len(skills)}


# ============ Storage/Update Tools ============


@mcp.tool()
async def store_context(
    content: str,
    context_type: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Store new context for future retrieval.
    Context will be embedded and indexed for semantic search.

    Args:
        content: The context content to store
        context_type: One of: task, iteration, skill, file, output, error
        tags: Optional tags for filtering
        metadata: Optional metadata dict

    Returns:
        id: ID of the stored context item
        stored: Whether storage was successful
    """
    if not context_store:
        return {"error": "Context store not initialized", "stored": False}

    try:
        ct = ContextType(context_type.lower())
    except ValueError:
        return {"error": f"Invalid context_type: {context_type}", "stored": False}

    try:
        item = await context_store.store(
            content=content,
            content_type=ct,
            tags=tags or [],
            metadata=metadata or {},
        )
        return {"id": item.id, "stored": True}
    except Exception as e:
        logger.error(f"Failed to store context: {e}")
        return {"error": str(e), "stored": False}


@mcp.tool()
async def mark_useful(
    item_id: str,
    helpful: bool,
    reason: Optional[str] = None,
) -> dict:
    """
    Provide feedback on context usefulness.
    This improves future retrieval accuracy by adjusting relevance scores.

    Args:
        item_id: ID of the context item to rate
        helpful: Whether the context was helpful (true/false)
        reason: Optional reason for the rating

    Returns:
        id: ID of the updated item
        updated: Whether update was successful
    """
    if not context_store:
        return {"error": "Context store not initialized", "updated": False}

    result = await context_store.update_usefulness(
        item_id=item_id,
        helpful=helpful,
        reason=reason,
    )

    if result:
        return {
            "id": item_id,
            "new_score": result.usefulness_score,
            "updated": True,
        }
    else:
        return {"id": item_id, "updated": False, "note": "Update pending"}


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
    error: Optional[str] = None,
) -> dict:
    """
    Store the result of a completed iteration.
    Called by the orchestrator after each iteration completes.

    Args:
        iteration: Iteration number (1-based)
        summary: Brief summary of what happened
        success: Whether the iteration succeeded
        duration_ms: Duration in milliseconds
        tokens_used: Number of tokens used
        cost: Cost in dollars
        tool_calls: List of tools that were called
        artifacts: List of files created/modified
        error: Error message if failed

    Returns:
        stored: Whether storage was successful
        iteration: The iteration number stored
    """
    if not context_store:
        return {"error": "Context store not initialized", "stored": False}

    result = IterationResult(
        iteration=iteration,
        success=success,
        summary=summary,
        duration_ms=duration_ms,
        tokens_used=tokens_used,
        cost=cost,
        tool_calls=tool_calls or [],
        artifacts=artifacts or [],
        error=error,
    )

    context_store.set_current_iteration(iteration)
    await context_store.store_iteration(result)

    return {"stored": True, "iteration": iteration}


# ============ Maintenance Tools ============


@mcp.tool()
async def summarize_old_context(older_than_iterations: int = 20) -> dict:
    """
    Compress old context items to summaries to save space.
    Older context is summarized to reduce storage while retaining key information.

    Args:
        older_than_iterations: Summarize items older than this many iterations

    Returns:
        summarized_count: Number of items summarized
    """
    if not context_store:
        return {"error": "Context store not initialized", "summarized_count": 0}

    count = await context_store.summarize_old(older_than_iterations)
    return {"summarized_count": count}


@mcp.tool()
async def prune_low_value_context(min_score: float = 0.3) -> dict:
    """
    Remove context items with low usefulness scores.
    Helps manage storage by removing context that wasn't helpful.

    Args:
        min_score: Remove items with scores below this threshold

    Returns:
        pruned_count: Number of items removed
    """
    if not context_store:
        return {"error": "Context store not initialized", "pruned_count": 0}

    count = await context_store.prune(min_score=min_score)
    return {"pruned_count": count}


# ============ Query/Analysis Tools ============


@mcp.tool()
async def get_context_stats() -> dict:
    """
    Get statistics about stored context.
    Useful for monitoring and debugging the context store.

    Returns:
        total_items: Total number of context items
        items_by_type: Count of items by type
        items_by_state: Count of items by state
        avg_usefulness_score: Average usefulness across all items
    """
    if not context_store:
        return {"error": "Context store not initialized"}

    stats = await context_store.get_stats()
    return stats.to_dict()


@mcp.tool()
async def health_check() -> dict:
    """
    Check MCP server health status.
    Returns status of all components.

    Returns:
        status: Overall health status
        db_connected: Whether database is connected
        context_count: Number of stored context items
    """
    if not context_store:
        return {
            "status": "unhealthy",
            "db_connected": False,
            "context_count": 0,
            "error": "Context store not initialized",
        }

    try:
        count = await context_store.count()
        return {
            "status": "healthy",
            "db_connected": context_store.is_connected(),
            "context_count": count,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "db_connected": False,
            "context_count": 0,
            "error": str(e),
        }


def main():
    """Run the MCP server."""
    # Initialize store before starting
    asyncio.get_event_loop().run_until_complete(initialize_store())

    # Run the MCP server
    transport = os.environ.get("RALPH_MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
