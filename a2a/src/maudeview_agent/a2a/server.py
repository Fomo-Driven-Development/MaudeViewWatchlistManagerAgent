"""A2A FastAPI server implementation."""

import json
import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import config
from .handler import task_handler
from .models import (
    JsonRpcRequest,
    Task,
    TaskCancelParams,
    TaskGetParams,
    TaskSendParams,
    TaskState,
    TaskStatus,
)

logger = logging.getLogger(__name__)

AGENT_CARD_PATH = Path(__file__).parent.parent.parent.parent / "agent-card.json"


def _load_agent_card() -> dict[str, Any]:
    """Load the agent card from JSON file."""
    if AGENT_CARD_PATH.exists():
        with open(AGENT_CARD_PATH) as f:
            return json.load(f)
    return {
        "name": "MaudeView Agent",
        "description": "TradingView chart control agent",
        "version": "1.0.0",
    }


async def _fetch_lmstudio_models() -> list[dict[str, Any]]:
    """Fetch loaded models from LM Studio's /api/v0/models endpoint."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{config.lmstudio_base_url.rstrip('/')}/api/v0/models",
        )
        resp.raise_for_status()
        all_models = resp.json().get("data", [])
        return [m for m in all_models if m.get("state") == "loaded"]


def create_a2a_app() -> FastAPI:
    """Create the A2A FastAPI application."""
    app = FastAPI(
        title="MaudeView Agent - A2A",
        description="Agent-to-Agent protocol server for TradingView chart control",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/.well-known/agent-card.json")
    async def get_agent_card():
        """Serve the A2A agent card for discovery."""
        return JSONResponse(content=_load_agent_card())

    @app.get("/agent-card.json")
    async def get_agent_card_alt():
        """Alternative path for agent card."""
        return JSONResponse(content=_load_agent_card())

    @app.post("/a2a")
    async def handle_a2a_request(request: Request):
        """Handle A2A JSON-RPC requests."""
        try:
            body = await request.json()
            rpc_request = JsonRpcRequest(**body)
        except Exception as e:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
            )

        try:
            result = await _handle_rpc_method(rpc_request)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": rpc_request.id,
                    "result": result,
                }
            )
        except Exception as e:
            logger.exception("Error handling A2A request")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": rpc_request.id,
                    "error": {"code": -32603, "message": str(e)},
                }
            )

    @app.get("/models")
    async def list_models():
        """List available LM Studio models."""
        if not config.is_lmstudio:
            return JSONResponse(
                content={"models": [], "note": "Backend is not LM Studio"},
            )
        models = await _fetch_lmstudio_models()
        return JSONResponse(content={"models": models})

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "agent": "maudeview-watchlist-manager"}

    return app


async def _handle_rpc_method(request: JsonRpcRequest) -> dict[str, Any]:
    """Route JSON-RPC method to handler."""
    method = request.method
    params = request.params

    if method == "tasks/send":
        return await _handle_tasks_send(params)
    elif method == "tasks/get":
        return await _handle_tasks_get(params)
    elif method == "tasks/cancel":
        return await _handle_tasks_cancel(params)
    elif method == "models/list":
        return await _handle_models_list()
    elif method == "agent/info":
        return _load_agent_card()
    else:
        raise ValueError(f"Unknown method: {method}")


async def _handle_tasks_send(params: dict[str, Any]) -> dict[str, Any]:
    """Handle tasks/send - create or continue a task."""
    send_params = TaskSendParams(**params)

    task_id = send_params.id
    if task_id and task_id in task_handler.tasks:
        task = task_handler.tasks[task_id]
    else:
        task = Task(status=TaskStatus(state=TaskState.SUBMITTED))
        task_handler.tasks[task.id] = task

    task = await task_handler.process_task(
        task, send_params.message, model=send_params.model
    )
    task_handler.tasks[task.id] = task

    return task.model_dump()


async def _handle_models_list() -> dict[str, Any]:
    """Handle models/list - return available LM Studio models."""
    if not config.is_lmstudio:
        return {"models": [], "note": "Backend is not LM Studio"}
    models = await _fetch_lmstudio_models()
    return {"models": models}


async def _handle_tasks_get(params: dict[str, Any]) -> dict[str, Any]:
    """Handle tasks/get - get task status."""
    get_params = TaskGetParams(**params)

    if get_params.id not in task_handler.tasks:
        raise ValueError(f"Task not found: {get_params.id}")

    task = task_handler.tasks[get_params.id]
    return task.model_dump()


async def _handle_tasks_cancel(params: dict[str, Any]) -> dict[str, Any]:
    """Handle tasks/cancel - cancel a task."""
    cancel_params = TaskCancelParams(**params)

    if cancel_params.id not in task_handler.tasks:
        raise ValueError(f"Task not found: {cancel_params.id}")

    task = task_handler.tasks[cancel_params.id]
    task.status = TaskStatus(state=TaskState.CANCELED)
    task_handler.tasks[task.id] = task

    return task.model_dump()


def run_a2a_server():
    """Run the A2A server."""
    import uvicorn

    app = create_a2a_app()
    uvicorn.run(
        app,
        host=config.a2a_host,
        port=config.a2a_port,
        log_level="info",
    )


if __name__ == "__main__":
    run_a2a_server()
