---
name: mcp-server-setup
description: Configure MCP server with Official MCP SDK, exposing stateless tools with authentication. Use when setting up the MCP server infrastructure for the AI chatbot.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# MCP Server Setup Skill

## Purpose

Configure the MCP (Model Context Protocol) server using the Official MCP SDK, exposing stateless tools with authentication, auto-generated documentation, and health monitoring.

## Used by

- mcp-server-specialist agent
- mcp-architect agent
- security-auditor agent

## When to Use

- Setting up the MCP server infrastructure
- Exposing MCP tools to AI agents
- Configuring authentication for tool endpoints
- Adding health checks and monitoring

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tools` | list | Yes | List of MCP tools to expose |
| `sdk_version` | string | Yes | MCP SDK version |
| `auth_config` | object | Yes | Authentication configuration |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `server_code` | Python code | FastAPI app for MCP server |
| `tool_exposure` | Python code | Endpoints for each tool |
| `docs` | JSON | OpenAPI specification |

## Core Implementation

### MCP Server

```python
# File: mcp/server.py
# [Skill]: MCP Server Setup

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from mcp.tools import ALL_TOOLS, TOOL_SCHEMAS
from mcp.auth import verify_token, get_current_user
from mcp.health import router as health_router
from app.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting MCP server...")
    init_db()
    yield
    logger.info("Shutting down MCP server...")


app = FastAPI(
    title="Todo MCP Server",
    description="MCP server exposing task management tools for AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health routes
app.include_router(health_router, prefix="/health", tags=["Health"])


@app.get("/")
async def root():
    """Server information endpoint."""
    return {
        "name": "Todo MCP Server",
        "version": "1.0.0",
        "tools_available": len(ALL_TOOLS)
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools with schemas."""
    return {
        "tools": TOOL_SCHEMAS,
        "count": len(TOOL_SCHEMAS)
    }
```

### Tool Exposure

```python
# File: mcp/routes/tools.py
# [Skill]: MCP Server Setup

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import logging

from mcp.auth import get_current_user
from mcp.tools import (
    add_task, list_tasks, complete_task,
    delete_task, update_task
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["Tools"])


# Request/Response models
class ToolInvocationRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class ToolInvocationResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Tool registry
TOOL_REGISTRY = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "update_task": update_task,
}


@router.post("/invoke", response_model=ToolInvocationResponse)
async def invoke_tool(
    request: ToolInvocationRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Invoke an MCP tool by name with arguments.

    The user_id is automatically injected from authentication.
    """
    tool_name = request.tool_name
    arguments = request.arguments

    logger.info(f"Tool invocation: {tool_name} by user {user_id}")

    # Validate tool exists
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    # Inject user_id into arguments
    arguments["user_id"] = user_id

    # Invoke tool
    try:
        tool_func = TOOL_REGISTRY[tool_name]
        result = tool_func(**arguments)

        logger.info(f"Tool {tool_name} succeeded for user {user_id}")

        return ToolInvocationResponse(
            success=True,
            result=result
        )

    except ValueError as e:
        logger.warning(f"Tool {tool_name} validation error: {e}")
        return ToolInvocationResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tool execution failed"
        )


# Individual tool endpoints for direct access
@router.post("/add_task")
async def add_task_endpoint(
    title: str,
    description: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Add a new task for the authenticated user."""
    return add_task(user_id=user_id, title=title, description=description)


@router.get("/list_tasks")
async def list_tasks_endpoint(
    status_filter: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """List all tasks for the authenticated user."""
    return list_tasks(user_id=user_id, status_filter=status_filter)


@router.post("/complete_task/{task_id}")
async def complete_task_endpoint(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Mark a task as completed."""
    return complete_task(user_id=user_id, task_id=task_id)


@router.delete("/delete_task/{task_id}")
async def delete_task_endpoint(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a task."""
    return delete_task(user_id=user_id, task_id=task_id)


@router.patch("/update_task/{task_id}")
async def update_task_endpoint(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Update a task's title or description."""
    return update_task(
        user_id=user_id,
        task_id=task_id,
        title=title,
        description=description
    )
```

### Authentication

```python
# File: mcp/auth.py
# [Skill]: MCP Server Setup

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# JWT configuration
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate user from JWT token.

    Args:
        credentials: Bearer token from request

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid or missing user_id
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub") or payload.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier"
        )

    return user_id


# Optional: API key authentication for server-to-server
async def verify_api_key(api_key: str) -> bool:
    """Verify API key for server-to-server communication."""
    expected_key = os.getenv("MCP_API_KEY")
    if not expected_key:
        logger.warning("MCP_API_KEY not configured")
        return False
    return api_key == expected_key
```

### Health Endpoints

```python
# File: mcp/health.py
# [Skill]: MCP Server Setup

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.database import engine
from sqlmodel import Session, text

logger = logging.getLogger(__name__)
router = APIRouter()

# Server start time for uptime calculation
_start_time = datetime.utcnow()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check including database connectivity.
    Returns 503 if not ready to accept traffic.
    """
    checks = {
        "database": False,
        "tools": False
    }

    # Check database
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Check tools are loaded
    from mcp.tools import ALL_TOOLS
    checks["tools"] = len(ALL_TOOLS) > 0

    # Overall status
    is_ready = all(checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks}
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live")
async def liveness_check():
    """Liveness check - is the server running?"""
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    return {
        "status": "alive",
        "uptime_seconds": uptime,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def metrics():
    """Basic metrics endpoint."""
    from mcp.tools import ALL_TOOLS

    return {
        "tools_count": len(ALL_TOOLS),
        "uptime_seconds": (datetime.utcnow() - _start_time).total_seconds(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Tools Index

```python
# File: mcp/tools/__init__.py
# [Skill]: MCP Server Setup

from .add_task import add_task
from .list_tasks import list_tasks
from .complete_task import complete_task
from .delete_task import delete_task
from .update_task import update_task
from .schemas import (
    add_task_schema,
    list_tasks_schema,
    complete_task_schema,
    delete_task_schema,
    update_task_schema,
    ALL_TOOL_SCHEMAS
)

# All available tools
ALL_TOOLS = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "update_task": update_task,
}

# Tool schemas for OpenAI
TOOL_SCHEMAS = ALL_TOOL_SCHEMAS

__all__ = [
    "add_task",
    "list_tasks",
    "complete_task",
    "delete_task",
    "update_task",
    "ALL_TOOLS",
    "TOOL_SCHEMAS",
]
```

### Application Entry Point

```python
# File: mcp/main.py
# [Skill]: MCP Server Setup

import uvicorn
import logging
import os

from mcp.server import app
from mcp.routes.tools import router as tools_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Include tool routes
app.include_router(tools_router)


def main():
    """Run the MCP server."""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8001"))

    uvicorn.run(
        "mcp.main:app",
        host=host,
        port=port,
        reload=os.getenv("ENV", "development") == "development"
    )


if __name__ == "__main__":
    main()
```

### Configuration

```python
# File: mcp/config.py
# [Skill]: MCP Server Setup

from pydantic_settings import BaseSettings
from typing import Optional


class MCPSettings(BaseSettings):
    """MCP Server configuration."""

    # Server
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    env: str = "development"

    # Auth
    better_auth_secret: str = "dev-secret-change-in-production"
    mcp_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./mcp.db"

    # Limits
    max_tools_per_request: int = 10
    request_timeout_seconds: int = 30

    class Config:
        env_file = ".env"


settings = MCPSettings()
```

## OpenAPI Documentation

The server auto-generates OpenAPI documentation at:
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI
- `/openapi.json` - Raw OpenAPI spec

## Quality Standards

### SDK Compliance
- Use official MCP SDK patterns
- Follow OpenAI tool schema format
- Stateless tool design

### Security
- JWT authentication on all tool endpoints
- User ID injection (not from client)
- API key option for server-to-server

### Documentation
- Auto-generated OpenAPI from FastAPI
- Descriptive endpoint summaries
- Request/response models

### Scalability
- Stateless design (no server session state)
- Database per-request sessions
- Horizontal scaling ready

### Monitoring
- `/health/` - Basic health
- `/health/ready` - Readiness with DB check
- `/health/live` - Liveness for k8s
- `/health/metrics` - Basic metrics

## Verification Checklist

- [ ] All tools exposed via `/tools/invoke` endpoint
- [ ] Individual endpoints for each tool
- [ ] JWT authentication configured
- [ ] User ID injected from token (not request)
- [ ] Health endpoints implemented
- [ ] OpenAPI docs auto-generated
- [ ] CORS configured
- [ ] Logging on all tool invocations
- [ ] Error responses follow standard format

## Output Format

1. **Server** in `mcp/server.py`
2. **Tool routes** in `mcp/routes/tools.py`
3. **Authentication** in `mcp/auth.py`
4. **Health checks** in `mcp/health.py`
5. **Entry point** in `mcp/main.py`
6. **Configuration** in `mcp/config.py`
