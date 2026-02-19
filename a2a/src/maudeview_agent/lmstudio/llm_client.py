"""Async client for LM Studio's Anthropic-compatible /v1/messages endpoint."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def mcp_tools_to_anthropic(mcp_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert MCP tool definitions to Anthropic tool_use format.

    Ensures every input_schema has a "properties" key — LM Studio requires it
    even for no-argument tools.
    """
    result = []
    for tool in mcp_tools:
        schema = dict(tool.get("inputSchema", {"type": "object"}))
        if "properties" not in schema:
            schema["properties"] = {}
        result.append({
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": schema,
        })
    return result


class LMStudioClient:
    """Async HTTP client for LM Studio's /v1/messages API."""

    def __init__(
        self,
        base_url: str,
        auth_token: str = "lmstudio",
        model: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.model = model
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(300.0, connect=10.0),
        )

    async def stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def send_messages(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """POST /v1/messages with Anthropic-compatible payload.

        Returns the parsed JSON response.
        """
        assert self._client is not None, "Client not started"

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "x-api-key": self.auth_token,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        logger.debug("LLM request: %d messages, %d tools", len(messages), len(tools))
        resp = await self._client.post("/v1/messages", json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.error(
                "LLM error %d: %s", resp.status_code, resp.text[:500]
            )
            resp.raise_for_status()
        data = resp.json()
        logger.debug("LLM response stop_reason=%s", data.get("stop_reason"))
        return data

    # -- context manager --

    async def __aenter__(self) -> "LMStudioClient":
        await self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()
