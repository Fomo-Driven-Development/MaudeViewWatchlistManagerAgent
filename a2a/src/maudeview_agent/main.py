"""Interactive CLI for the MaudeView Agent."""

import asyncio
import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from .config import config
from .prompts import ALLOWED_TOOLS, MCP_SERVER_NAME, SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _build_options() -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with the Go MCP server as a subprocess."""
    return ClaudeAgentOptions(
        mcp_servers={
            MCP_SERVER_NAME: {
                "type": "stdio",
                "command": str(config.mcp_binary_path),
                "env": {"CONTROLLER_BIND_ADDR": config.controller_bind_addr},
            }
        },
        allowed_tools=ALLOWED_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


async def run_interactive_chat():
    """Run an interactive multi-turn chat session."""
    options = _build_options()

    print("MaudeView Agent")
    print("=" * 50)
    print("Control TradingView charts via natural language.")
    print("Type 'quit' or 'exit' to end the session.")
    print("=" * 50)
    print()

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            if not user_input:
                continue

            await client.query(user_input)

            print()
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Assistant: {block.text}")
                        elif isinstance(block, ToolUseBlock):
                            print(f"[Using tool: {block.name}]")
                elif isinstance(msg, ResultMessage):
                    if msg.total_cost_usd:
                        print(f"\n[Cost: ${msg.total_cost_usd:.6f}]")
            print()


def main():
    """Entry point for interactive CLI."""
    try:
        asyncio.run(run_interactive_chat())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
