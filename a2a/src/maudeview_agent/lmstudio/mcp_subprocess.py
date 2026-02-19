"""MCP subprocess manager — spawn Go binary, speak JSON-RPC 2.0 over stdio."""

import asyncio
import json
import logging
import signal
from typing import Any

logger = logging.getLogger(__name__)


class MCPSubprocess:
    """Async context manager that runs an MCP server as a child process.

    Speaks JSON-RPC 2.0 over stdin/stdout (newline-delimited JSON).
    """

    def __init__(self, binary_path: str, env: dict[str, str] | None = None):
        self.binary_path = binary_path
        self.env = env
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self._tools: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def start(self) -> list[dict[str, Any]]:
        """Spawn the MCP binary and perform the initialize handshake.

        Returns the list of tools from tools/list.
        """
        import os

        merged_env = {**os.environ, **(self.env or {})}
        self._process = await asyncio.create_subprocess_exec(
            self.binary_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )
        logger.info("MCP subprocess started (pid=%d)", self._process.pid)

        # Initialize handshake
        init_result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "maudeview-lmstudio", "version": "0.1.0"},
        })
        logger.debug("MCP initialize result: %s", init_result)

        # Send initialized notification
        await self._send_notification("notifications/initialized", {})

        # Get tool list
        tools_result = await self._send_request("tools/list", {})
        self._tools = tools_result.get("tools", [])
        logger.info("MCP server exposes %d tools", len(self._tools))
        return self._tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> tuple[str, bool]:
        """Execute a tool via tools/call.

        Returns (content_text, is_error).
        """
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })
        is_error = result.get("isError", False)
        content_parts = result.get("content", [])
        text_parts = [
            p.get("text", "") for p in content_parts if p.get("type") == "text"
        ]
        return "\n".join(text_parts), is_error

    async def stop(self) -> None:
        """Gracefully stop the MCP subprocess."""
        if self._process is None or self._process.returncode is not None:
            return

        try:
            self._process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("MCP subprocess did not exit, sending SIGKILL")
                self._process.kill()
                await self._process.wait()
        except ProcessLookupError:
            pass
        logger.info("MCP subprocess stopped")

    @property
    def tools(self) -> list[dict[str, Any]]:
        return self._tools

    # -- internal JSON-RPC helpers --

    async def _send_request(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for the response."""
        async with self._lock:
            self._request_id += 1
            req_id = self._request_id
            message = {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params,
            }
            await self._write(message)
            return await self._read_response(req_id)

    async def _send_notification(
        self, method: str, params: dict[str, Any]
    ) -> None:
        """Send a JSON-RPC notification (no id, no response expected)."""
        async with self._lock:
            message = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }
            await self._write(message)

    async def _write(self, message: dict[str, Any]) -> None:
        assert self._process and self._process.stdin
        line = json.dumps(message) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

    async def _read_response(self, expected_id: int) -> dict[str, Any]:
        assert self._process and self._process.stdout
        while True:
            raw = await self._process.stdout.readline()
            if not raw:
                raise RuntimeError("MCP subprocess stdout closed unexpectedly")
            line = raw.decode().strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                logger.debug("Skipping non-JSON line from MCP: %s", line[:200])
                continue

            # Skip notifications (no id)
            if "id" not in msg:
                logger.debug("MCP notification: %s", msg.get("method", "?"))
                continue

            if msg["id"] != expected_id:
                logger.warning(
                    "Unexpected response id %s (expected %s)", msg["id"], expected_id
                )
                continue

            if "error" in msg and msg["error"] is not None:
                err = msg["error"]
                raise RuntimeError(
                    f"MCP error {err.get('code')}: {err.get('message')}"
                )
            return msg.get("result", {})

    # -- context manager --

    async def __aenter__(self) -> "MCPSubprocess":
        await self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.stop()
