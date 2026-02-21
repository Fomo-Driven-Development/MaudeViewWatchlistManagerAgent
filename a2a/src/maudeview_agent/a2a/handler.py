"""Task handler for A2A tasks — dispatches to Claude or LM Studio backend."""

import logging
import time

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)

from ..config import config
from ..options import build_claude_options
from .models import Message, Task, TaskState, TaskStatus, TextPart

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handles A2A tasks by delegating to Claude or LM Studio with MCP tools."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}

    async def process_task(
        self, task: Task, message: Message, model: str | None = None
    ) -> Task:
        """Process a task by sending the user message to the configured backend."""
        task.history.append(message)
        task.status = TaskStatus(state=TaskState.WORKING)

        try:
            user_text = " ".join(
                p.text for p in message.parts if hasattr(p, "text")
            )
            backend = "lmstudio" if config.is_lmstudio else "claude"
            logger.info("Processing task %s — backend=%s, prompt=%r", task.id, backend, user_text[:200])

            if config.is_lmstudio:
                response_text = await self._query_lmstudio(user_text, model=model)
            else:
                response_text = await self._query_claude(user_text)

            logger.info("Task %s completed — response length=%d chars", task.id, len(response_text))
            agent_message = Message(
                role="agent", parts=[TextPart(text=response_text)]
            )
            task.history.append(agent_message)
            task.status = TaskStatus(
                state=TaskState.COMPLETED, message=agent_message
            )
        except Exception as e:
            logger.exception("Error processing task %s", task.id)
            error_message = Message(
                role="agent", parts=[TextPart(text=f"Error: {e}")]
            )
            task.status = TaskStatus(
                state=TaskState.FAILED, message=error_message
            )

        return task

    async def _query_claude(self, prompt: str) -> str:
        """Send prompt to Claude with MCP tools, collect response text."""
        options = build_claude_options(permission_mode="bypassPermissions")

        full_result = ""
        text_parts: list[str] = []
        t0 = time.monotonic()
        t_first_msg = None

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                elapsed = time.monotonic() - t0
                if t_first_msg is None:
                    t_first_msg = elapsed
                    logger.info("First message at %.1fs", elapsed)

                if isinstance(message, SystemMessage):
                    if message.subtype == "init":
                        for s in message.data.get("mcp_servers", []):
                            logger.info("MCP '%s': status=%s", s.get("name", "?"), s.get("status", "?"))

                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            input_preview = str(block.input)[:300] if block.input else ""
                            logger.info("%.1fs Tool call: %s — %s", elapsed, block.name, input_preview)
                        elif isinstance(block, TextBlock):
                            logger.info("%.1fs Text: %s", elapsed, block.text[:200])
                            text_parts.append(block.text)
                        elif isinstance(block, ToolResultBlock):
                            status = "error" if block.is_error else "ok"
                            preview = str(block.content)[:500] if block.content else ""
                            logger.info("%.1fs Tool result [%s]: %s", elapsed, status, preview)

                elif isinstance(message, ResultMessage):
                    if message.subtype == "success":
                        full_result = message.result or ""
                        logger.info("%.1fs Done — %d turns, cost=$%s", elapsed, message.num_turns, message.total_cost_usd)
                    else:
                        logger.error("%.1fs Agent error (subtype=%s): %s", elapsed, message.subtype, message.result)
                        full_result = message.result or ""

        total = time.monotonic() - t0
        logger.info("Total wall time: %.1fs", total)

        return full_result or "\n".join(text_parts) or "No response generated."

    async def _query_lmstudio(self, prompt: str, model: str | None = None) -> str:
        """Send prompt to LM Studio with MCP tools, collect response text."""
        from ..lmstudio import LMStudioAgent

        async with LMStudioAgent(model=model) as agent:
            response = await agent.query(prompt)
            return response.text


task_handler = TaskHandler()
