"""Task handler using Claude Agent SDK to process A2A tasks."""

import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)

from ..config import config
from ..prompts import ALLOWED_TOOLS, MCP_SERVER_NAME, SYSTEM_PROMPT
from .models import Message, Task, TaskState, TaskStatus, TextPart

logger = logging.getLogger(__name__)


class TaskHandler:
    """Handles A2A tasks by delegating to Claude with MCP tools."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}

    async def process_task(self, task: Task, message: Message) -> Task:
        """Process a task by sending the user message to Claude with MCP tools."""
        task.history.append(message)
        task.status = TaskStatus(state=TaskState.WORKING)

        try:
            user_text = " ".join(
                p.text for p in message.parts if hasattr(p, "text")
            )
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
        options = ClaudeAgentOptions(
            mcp_servers={
                MCP_SERVER_NAME: {
                    "type": "stdio",
                    "command": str(config.mcp_binary_path),
                    "env": {
                        "CONTROLLER_BIND_ADDR": config.controller_bind_addr,
                    },
                }
            },
            allowed_tools=ALLOWED_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            permission_mode="bypassPermissions",
        )

        result_parts = []
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            result_parts.append(block.text)

        return "\n".join(result_parts) if result_parts else "No response generated."


task_handler = TaskHandler()
