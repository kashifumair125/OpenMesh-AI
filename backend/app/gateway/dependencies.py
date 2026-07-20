"""OpenMesh AI - Gateway Dependencies"""

from fastapi import Request, HTTPException, Depends
from app.config import get_settings, Settings
from app.registry.service import ToolRegistry
from app.memory.store import MemoryStore


def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


def get_tool_registry(request: Request) -> ToolRegistry:
    """Get tool registry from app state."""
    return request.app.state.tool_registry


def get_memory_store(request: Request) -> MemoryStore:
    """Get memory store from app state."""
    return request.app.state.memory_store
