"""Interactive CLI for the MaudeView Agent."""

import asyncio
import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

from .config import config
from .options import build_claude_options

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def _run_claude_chat() -> None:
    """Interactive chat loop using Claude Agent SDK."""
    options = build_claude_options()

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


async def _run_lmstudio_chat() -> None:
    """Interactive chat loop using LM Studio direct backend."""
    from .lmstudio import LMStudioAgent

    async with LMStudioAgent() as agent:
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

            print()
            response = await agent.query(user_input)
            if response.tool_calls_made:
                print(f"[Tools used: {', '.join(response.tool_calls_made)}]")
            print(f"Assistant: {response.text}")
            print()


async def run_interactive_chat() -> None:
    """Run an interactive multi-turn chat session."""
    print("MaudeView Agent")
    print("=" * 50)
    print(f"Backend: {config.backend_label}")
    print("Control TradingView charts via natural language.")
    print("Type 'quit' or 'exit' to end the session.")
    print("=" * 50)
    print()

    if config.is_lmstudio:
        await _run_lmstudio_chat()
    else:
        await _run_claude_chat()


def main():
    """Entry point for interactive CLI."""
    try:
        asyncio.run(run_interactive_chat())
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
