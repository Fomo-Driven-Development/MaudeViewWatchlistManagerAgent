# MaudeView Watchlist Manager Agent
# Go MCP server + Python A2A layer

set dotenv-load

# Show available commands
help:
	@echo "MaudeView Watchlist Manager Agent"
	@echo ""
	@echo "  Build"
	@echo "    just build              Build the Go MCP binary"
	@echo "    just install            Install Python A2A package (editable)"
	@echo "    just install-controller Install tv_controller binary from MaudeViewTVCore"
	@echo "    just setup              Full setup (build + install + controller)"
	@echo ""
	@echo "  Run"
	@echo "    just run-tv-controller-with-browser  Launch browser + tv_controller"
	@echo "    just agent              Interactive CLI (Claude + MCP tools)"
	@echo "    just a2a                Start A2A server on :8100"
	@echo "    just mcp                Run Go MCP server directly (stdio)"
	@echo ""
	@echo "  Dev"
	@echo "    just clean              Remove build artifacts"
	@echo ""

# Build the Go MCP binary
build:
	go build -o ./bin/agent .

# Install Python A2A package in editable mode
install:
	cd a2a && uv sync

# Install tv_controller binary from latest MaudeViewTVCore release
install-controller:
    #!/usr/bin/env bash
    set -euo pipefail
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    [ "$ARCH" = "x86_64" ] && ARCH="amd64"
    [ "$ARCH" = "aarch64" ] && ARCH="arm64"
    mkdir -p bin
    echo "Downloading tv_controller (${OS}/${ARCH})..."
    curl -fsSL "https://github.com/Fomo-Driven-Development/MaudeViewTVCore/releases/latest/download/tv_controller_${OS}_${ARCH}" \
        -o bin/tv_controller
    chmod +x bin/tv_controller
    echo "Done."

# Full setup: build Go binary + install Python package + install controller
setup: build install install-controller

# Launch browser + tv_controller (single command)
run-tv-controller-with-browser:
	CONTROLLER_LAUNCH_BROWSER=true ./bin/tv_controller

# Run interactive CLI (Claude Agent SDK + Go MCP subprocess)
agent:
	cd a2a && uv run maudeview-agent

# Start A2A JSON-RPC server
a2a:
	cd a2a && uv run maudeview-agent-a2a

# Run Go MCP server directly (stdio, for debugging)
mcp:
	./bin/agent

# Remove build artifacts
clean:
	rm -rf bin/
	rm -rf a2a/.venv
