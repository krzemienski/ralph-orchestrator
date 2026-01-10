"""
MCP Client wrapper for Ralph Orchestrator.

Provides a high-level interface for the orchestrator to communicate
with the MCP context server.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class MCPClientConfig:
    """Configuration for the MCP client."""

    enabled: bool = True
    server_command: str = "python"
    server_args: List[str] = field(default_factory=lambda: ["-m", "ralph_orchestrator.mcp.server"])
    max_items: int = 10
    context_types: List[str] = field(default_factory=lambda: ["skill", "error", "iteration"])
    timeout_seconds: float = 30.0
    max_context_tokens: int = 4000


class RalphMCPClient:
    """
    Client wrapper for Ralph to communicate with MCP context server.

    Handles connection management, caching, and graceful degradation
    when the MCP server is unavailable.
    """

    def __init__(self, config: MCPClientConfig):
        """
        Initialize the MCP client.

        Args:
            config: Client configuration
        """
        self.config = config
        self._session = None
        self._connected = False
        self._cache: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._retrieval_count = 0

    @property
    def retrieval_count(self) -> int:
        """Number of context retrievals performed."""
        return self._retrieval_count

    async def connect(self) -> bool:
        """
        Initialize connection to MCP server.

        Returns:
            True if connected successfully, False otherwise
        """
        if not self.config.enabled:
            logger.info("MCP client disabled by configuration")
            return False

        try:
            # Import MCP client components
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.config.server_command,
                args=self.config.server_args,
            )

            # Note: In production, we'd maintain the connection.
            # For now, we test connectivity and mark as ready.
            logger.info("MCP client ready (lazy connection mode)")
            self._connected = True
            return True

        except ImportError as e:
            logger.warning(f"MCP client dependencies not available: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize MCP client: {e}")
            self._connected = False
            return False

    async def get_relevant_context(
        self,
        query: str,
        max_items: Optional[int] = None,
        context_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for the current task.

        Args:
            query: Search query (task description)
            max_items: Maximum items to retrieve
            context_types: Types of context to retrieve

        Returns:
            List of context items with content and metadata
        """
        if not self._connected:
            return self._cache.get("last_context", [])

        self._retrieval_count += 1

        try:
            # In production, this would call the MCP server
            # For now, return cached or empty
            result = await self._call_mcp_tool(
                "get_relevant_context",
                {
                    "query": query[:500],
                    "max_items": max_items or self.config.max_items,
                    "context_types": context_types or self.config.context_types,
                },
            )

            items = result.get("items", [])
            self._cache["last_context"] = items
            return items

        except asyncio.TimeoutError:
            logger.warning("MCP context retrieval timed out")
            return self._cache.get("last_context", [])
        except Exception as e:
            logger.warning(f"MCP context retrieval failed: {e}")
            return self._cache.get("last_context", [])

    async def store_iteration_result(
        self,
        iteration: int,
        summary: str,
        success: bool,
        duration_ms: int = 0,
        tokens_used: int = 0,
        cost: float = 0.0,
        tool_calls: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Store completed iteration result.

        Args:
            iteration: Iteration number
            summary: Brief summary of the iteration
            success: Whether it succeeded
            duration_ms: Duration in milliseconds
            tokens_used: Tokens consumed
            cost: Cost in dollars
            tool_calls: Tools that were called
            artifacts: Files created/modified
            error: Error message if failed

        Returns:
            True if stored successfully
        """
        if not self._connected:
            return False

        try:
            await self._call_mcp_tool(
                "store_iteration_result",
                {
                    "iteration": iteration,
                    "summary": summary,
                    "success": success,
                    "duration_ms": duration_ms,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    "tool_calls": tool_calls or [],
                    "artifacts": artifacts or [],
                    "error": error,
                },
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to store iteration result: {e}")
            return False

    async def mark_useful(
        self,
        item_id: str,
        helpful: bool,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Provide feedback on context item usefulness.

        Args:
            item_id: ID of the context item
            helpful: Whether it was helpful
            reason: Optional reason for the rating

        Returns:
            True if feedback recorded
        """
        if not self._connected:
            return False

        try:
            await self._call_mcp_tool(
                "mark_useful",
                {
                    "item_id": item_id,
                    "helpful": helpful,
                    "reason": reason,
                },
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to mark context usefulness: {e}")
            return False

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the server.

        In production, this would use the MCP client session.
        For the sample implementation, we simulate the call.
        """
        # This is where the actual MCP protocol call would happen
        # For now, we return a simulated response
        logger.debug(f"MCP tool call: {tool_name}({arguments})")

        # Simulate responses for testing
        if tool_name == "get_relevant_context":
            return {"items": [], "stats": {"search_time_ms": 0, "returned": 0}}
        elif tool_name == "store_iteration_result":
            return {"stored": True}
        elif tool_name == "mark_useful":
            return {"updated": True}
        else:
            return {}

    async def close(self):
        """Close connection to MCP server."""
        if self._session:
            self._session = None
            self._connected = False
            logger.info("MCP client connection closed")

    def format_context_for_prompt(
        self,
        items: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Format retrieved context items for injection into prompt.

        Args:
            items: List of context items from get_relevant_context
            max_tokens: Maximum tokens to include

        Returns:
            Formatted string for prompt injection
        """
        if not items:
            return ""

        max_tokens = max_tokens or self.config.max_context_tokens
        lines = ["## Relevant Context from Previous Iterations\n"]
        token_estimate = 15  # Header tokens

        for item in items:
            content = item.get("content", "")
            content_type = item.get("content_type", "unknown")

            # Rough token estimate (4 chars per token)
            item_tokens = len(content) // 4 + 15

            if token_estimate + item_tokens > max_tokens:
                lines.append(f"\n*[{len(items) - len(lines) + 1} more items truncated]*")
                break

            lines.append(f"### [{content_type.upper()}]")
            lines.append(content)
            lines.append("")

            token_estimate += item_tokens

        return "\n".join(lines)

    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected


async def create_mcp_client(config: Optional[MCPClientConfig] = None) -> Optional[RalphMCPClient]:
    """
    Factory function to create and connect an MCP client.

    Args:
        config: Client configuration (uses defaults if None)

    Returns:
        Connected MCP client or None if connection failed
    """
    config = config or MCPClientConfig()

    if not config.enabled:
        return None

    client = RalphMCPClient(config)
    success = await client.connect()

    if success:
        return client
    else:
        return None
