"""Configuration for MaudeView Agent."""

from dataclasses import dataclass
from os import environ
from pathlib import Path


@dataclass
class Config:
    """Agent configuration with environment variable support."""

    controller_bind_addr: str = "127.0.0.1:8188"
    mcp_binary_path: Path = Path("../bin/agent")
    a2a_host: str = "0.0.0.0"
    a2a_port: int = 8100
    a2a_url: str = "http://localhost:8100/a2a"

    # Backend selection: "claude" or "lmstudio"
    agent_backend: str = "claude"
    lmstudio_base_url: str = "http://llm2-studio.lan:1234"
    lmstudio_auth_token: str = "lmstudio"
    lmstudio_model: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        raw_path = environ.get("MCP_BINARY_PATH", str(cls.mcp_binary_path))
        resolved = Path(raw_path)
        if not resolved.is_absolute():
            resolved = (Path.cwd() / raw_path).resolve()

        return cls(
            controller_bind_addr=environ.get(
                "CONTROLLER_BIND_ADDR", cls.controller_bind_addr
            ),
            mcp_binary_path=resolved,
            a2a_host=environ.get("A2A_HOST", cls.a2a_host),
            a2a_port=int(environ.get("A2A_PORT", str(cls.a2a_port))),
            a2a_url=environ.get("A2A_URL", cls.a2a_url),
            agent_backend=environ.get("AGENT_BACKEND", cls.agent_backend),
            lmstudio_base_url=environ.get(
                "LMSTUDIO_BASE_URL", cls.lmstudio_base_url
            ),
            lmstudio_auth_token=environ.get(
                "LMSTUDIO_AUTH_TOKEN", cls.lmstudio_auth_token
            ),
            lmstudio_model=environ.get("LMSTUDIO_MODEL", cls.lmstudio_model),
        )

    @property
    def is_lmstudio(self) -> bool:
        return self.agent_backend == "lmstudio"

    @property
    def backend_label(self) -> str:
        if self.is_lmstudio:
            model = self.lmstudio_model or "(default)"
            return f"LM Studio ({self.lmstudio_base_url}, model={model})"
        return "Claude (Anthropic API)"


config = Config.from_env()
