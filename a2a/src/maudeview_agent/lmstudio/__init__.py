"""LM Studio direct backend — bypasses claude CLI, manages MCP + tool loop."""

from .agent import LMStudioAgent

__all__ = ["LMStudioAgent"]
