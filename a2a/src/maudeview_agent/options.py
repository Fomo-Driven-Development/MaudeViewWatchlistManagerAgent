"""Shared ClaudeAgentOptions builder for all entry points."""

from claude_agent_sdk import ClaudeAgentOptions

from .config import config
from .prompts import ALLOWED_TOOLS, MCP_SERVER_NAME, SYSTEM_PROMPT


def build_claude_options(**overrides) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with backend-aware env/model injection.

    When AGENT_BACKEND=lmstudio, injects ANTHROPIC_BASE_URL and
    ANTHROPIC_AUTH_TOKEN into the subprocess env and sets the model.

    Extra keyword arguments (e.g. permission_mode) are forwarded to
    ClaudeAgentOptions.
    """
    env: dict[str, str] = {}
    model: str | None = None

    if config.is_lmstudio:
        env["ANTHROPIC_BASE_URL"] = config.lmstudio_base_url
        env["ANTHROPIC_AUTH_TOKEN"] = config.lmstudio_auth_token
        if config.lmstudio_model:
            model = config.lmstudio_model

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
        model=model,
        env=env,
        **overrides,
    )
