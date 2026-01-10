"""
MCP Context Server for Progressive Context Disclosure.

This module provides an MCP (Model Context Protocol) server that enables
semantic retrieval of relevant context across Ralph orchestrator iterations.

Components:
- server: FastMCP-based context server with tools for storage/retrieval
- client: Client wrapper for orchestrator integration
- store: LanceDB-backed vector storage with semantic search
- models: Data classes for context items and results
"""

from ralph_orchestrator.mcp.models import (
    ContextType,
    ContextState,
    ContextItem,
    IterationResult,
    RetrievalResult,
)

__all__ = [
    "ContextType",
    "ContextState",
    "ContextItem",
    "IterationResult",
    "RetrievalResult",
]
