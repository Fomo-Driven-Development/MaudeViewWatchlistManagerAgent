"""LM Studio agent loop — LLM call, tool dispatch via MCP, repeat."""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import config
from ..prompts import ALLOWED_TOOLS, SYSTEM_PROMPT
from .llm_client import LMStudioClient, mcp_tools_to_anthropic
from .mcp_subprocess import MCPSubprocess

logger = logging.getLogger(__name__)

# Bare tool names allowed (strip mcp__maudeview__ prefix)
_ALLOWED_BARE = {t.split("__")[-1] for t in ALLOWED_TOOLS}


@dataclass
class AgentResponse:
    """Result from one agent query."""

    text: str
    tool_calls_made: list[str] = field(default_factory=list)


class LMStudioAgent:
    """Manages MCP subprocess + LM Studio LLM and runs the tool-calling loop."""

    def __init__(
        self,
        mcp_binary: str | None = None,
        base_url: str | None = None,
        auth_token: str | None = None,
        model: str | None = None,
    ):
        self._mcp_binary = mcp_binary or str(config.mcp_binary_path)
        self._base_url = base_url or config.lmstudio_base_url
        self._auth_token = auth_token or config.lmstudio_auth_token
        self._model = model or config.lmstudio_model

        self._mcp: MCPSubprocess | None = None
        self._llm: LMStudioClient | None = None
        self._tools_anthropic: list[dict[str, Any]] = []

    async def start(self) -> None:
        """Start MCP subprocess and LLM client, fetch and filter tools."""
        self._mcp = MCPSubprocess(
            self._mcp_binary,
            env={"CONTROLLER_BIND_ADDR": config.controller_bind_addr},
        )
        mcp_tools = await self._mcp.start()

        # Filter to allowed tools
        filtered = [t for t in mcp_tools if t["name"] in _ALLOWED_BARE]
        self._tools_anthropic = mcp_tools_to_anthropic(filtered)
        logger.info(
            "Filtered %d/%d MCP tools for LLM", len(filtered), len(mcp_tools)
        )

        self._llm = LMStudioClient(
            base_url=self._base_url,
            auth_token=self._auth_token,
            model=self._model,
        )
        await self._llm.start()

    async def stop(self) -> None:
        """Shut down LLM client and MCP subprocess."""
        if self._llm:
            await self._llm.stop()
        if self._mcp:
            await self._mcp.stop()

    async def query(self, user_message: str, max_turns: int = 50) -> AgentResponse:
        """Run the agentic loop: LLM call -> tool dispatch -> repeat.

        Returns when the LLM produces a text response with no tool_use blocks,
        or max_turns is reached.
        """
        assert self._llm and self._mcp, "Agent not started"

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message},
        ]
        tool_calls_made: list[str] = []

        for turn in range(max_turns):
            response = await self._llm.send_messages(
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=self._tools_anthropic,
            )

            content = response.get("content", [])
            stop_reason = response.get("stop_reason", "")

            # Append assistant message
            messages.append({"role": "assistant", "content": content})

            # Extract tool_use blocks
            tool_uses = [b for b in content if b.get("type") == "tool_use"]

            if not tool_uses:
                # No more tool calls — extract final text
                text_parts = [
                    b.get("text", "")
                    for b in content
                    if b.get("type") == "text"
                ]
                return AgentResponse(
                    text="\n".join(text_parts) or "(no text response)",
                    tool_calls_made=tool_calls_made,
                )

            # Execute each tool and build tool_result blocks
            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                tool_name = tu["name"]
                tool_input = tu.get("input", {})
                tool_id = tu["id"]

                logger.info("Tool call: %s(%s)", tool_name, json.dumps(tool_input)[:200])
                tool_calls_made.append(tool_name)

                try:
                    text, is_error = await self._mcp.call_tool(tool_name, tool_input)
                except Exception as e:
                    text = f"MCP error: {e}"
                    is_error = True
                    logger.exception("MCP call_tool failed: %s", tool_name)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": text,
                    "is_error": is_error,
                })

            messages.append({"role": "user", "content": tool_results})
            logger.debug(
                "Turn %d: %d tool calls, stop_reason=%s",
                turn + 1, len(tool_uses), stop_reason,
            )

        return AgentResponse(
            text="(max turns reached without final response)",
            tool_calls_made=tool_calls_made,
        )

    # -- context manager --

    async def __aenter__(self) -> "LMStudioAgent":
        await self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()
