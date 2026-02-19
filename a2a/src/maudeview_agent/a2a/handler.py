"""Task handler for A2A tasks — dispatches to Claude or LM Studio backend."""

import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    TextBlock,
)

from ..config import config
from ..options import build_claude_options
from .models import Message, Task, TaskState, TaskStatus, TextPart

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handles A2A tasks by delegating to Claude or LM Studio with MCP tools."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}

    async def process_task(self, task: Task, message: Message) -> Task:
        """Process a task by sending the user message to the configured backend."""
        task.history.append(message)
        task.status = TaskStatus(state=TaskState.WORKING)

        try:
            user_text = " ".join(
                p.text for p in message.parts if hasattr(p, "text")
            )

            if config.is_lmstudio:
                response_text = await self._query_lmstudio(user_text)
            else:
                response_text = await self._query_claude(user_text)

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

        result_parts = []
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            result_parts.append(block.text)

        return "\n".join(result_parts) if result_parts else "No response generated."

    async def _query_lmstudio(self, prompt: str) -> str:
        """Send prompt to LM Studio with MCP tools, collect response text."""
        from ..lmstudio import LMStudioAgent

        async with LMStudioAgent() as agent:
            response = await agent.query(prompt)
            return response.text


task_handler = TaskHandler()
