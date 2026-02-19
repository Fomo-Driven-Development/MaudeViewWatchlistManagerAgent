"""A2A protocol models based on the Agent2Agent specification."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """Task lifecycle states."""

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TextPart(BaseModel):
    """Text content part."""

    type: str = "text"
    text: str


class Message(BaseModel):
    """A2A message in a task."""

    role: str  # "user" or "agent"
    parts: list[TextPart]


class TaskStatus(BaseModel):
    """Current status of a task."""

    state: TaskState
    message: Message | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Task(BaseModel):
    """A2A task representation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    status: TaskStatus
    history: list[Message] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


# JSON-RPC Models


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request."""

    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response."""

    jsonrpc: str = "2.0"
    id: str | int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Any = None


# A2A specific params


class TaskSendParams(BaseModel):
    """Parameters for tasks/send method."""

    message: Message
    id: str | None = None
    model: str | None = None


class TaskGetParams(BaseModel):
    """Parameters for tasks/get method."""

    id: str


class TaskCancelParams(BaseModel):
    """Parameters for tasks/cancel method."""

    id: str
