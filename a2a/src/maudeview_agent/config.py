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

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        raw_path = environ.get("MCP_BINARY_PATH", str(cls.mcp_binary_path))
        resolved = Path(raw_path)
        if not resolved.is_absolute():
            resolved = (Path(__file__).parent.parent.parent.parent / raw_path).resolve()

        return cls(
            controller_bind_addr=environ.get(
                "CONTROLLER_BIND_ADDR", cls.controller_bind_addr
            ),
            mcp_binary_path=resolved,
            a2a_host=environ.get("A2A_HOST", cls.a2a_host),
            a2a_port=int(environ.get("A2A_PORT", str(cls.a2a_port))),
        )


config = Config.from_env()
