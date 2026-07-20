"""OpenMesh AI - Gateway API Router (Minimal)"""

import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import Settings, get_settings
from app.gateway.models import (
    ChatRequest, ChatResponse, ToolDiscoveryRequest, ToolInfo,
    WorkflowRequest, WorkflowResponse, DashboardMetrics, ToolCall
)
from app.gateway.dependencies import get_tool_registry, get_memory_store
from app.planner.agent import PlannerAgent
from app.models.gateway import ModelGateway
from app.registry.service import ToolRegistry
from app.memory.store import MemoryStore

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    registry: ToolRegistry = Depends(get_tool_registry),
    memory: MemoryStore = Depends(get_memory_store),
):
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    model_gateway = ModelGateway(
        provider=request.model_provider or settings.DEFAULT_MODEL_PROVIDER,
        settings=settings
    )
    planner = PlannerAgent(
        model_gateway=model_gateway,
        registry=registry,
        memory=memory
    )

    try:
        result = await planner.execute(
            message=request.message,
            session_id=session_id,
            requested_tools=request.tools
        )

        latency_ms = (time.time() - start_time) * 1000

        return ChatResponse(
            response=result["response"],
            model_used=result["model_used"],
            provider=result["provider"],
            tools_called=[ToolCall(**t) for t in result.get("tools_called", [])],
            cost=result["cost"],
            latency_ms=latency_ms,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/discover", response_model=list[ToolInfo])
async def discover_tools(
    request: ToolDiscoveryRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
):
    tools = await registry.discover(query=request.query, top_k=request.top_k)
    return [ToolInfo(**t) for t in tools]


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools(
    registry: ToolRegistry = Depends(get_tool_registry),
):
    tools = await registry.list_all()
    return [ToolInfo(**t) for t in tools]


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowRequest,
    settings: Settings = Depends(get_settings),
    registry: ToolRegistry = Depends(get_tool_registry),
    memory: MemoryStore = Depends(get_memory_store),
):
    """Create and execute a multi-step workflow."""
    model_gateway = ModelGateway(
        provider=request.model_provider or settings.DEFAULT_MODEL_PROVIDER,
        settings=settings
    )
    
    from app.planner.workflows import WorkflowEngine
    engine = WorkflowEngine(model_gateway=model_gateway, memory=memory)
    
    result = await engine.execute(
        name=request.name,
        description=request.description,
        inputs=request.inputs
    )
    
    return WorkflowResponse(**result)


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    memory: MemoryStore = Depends(get_memory_store),
):
    workflow = await memory.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowResponse(**workflow)


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    memory: MemoryStore = Depends(get_memory_store),
):
    metrics = await memory.get_metrics()
    return DashboardMetrics(**metrics)


@router.get("/models")
async def list_models(
    settings: Settings = Depends(get_settings),
):
    return {
        "providers": [
            {"id": "ollama", "name": "Ollama (Local)", "status": "available", "cost": "FREE", "model": settings.OLLAMA_MODEL},
            {"id": "claude", "name": "Claude (Anthropic)", "status": "available" if settings.ANTHROPIC_API_KEY else "needs_api_key", "cost": "Free tier", "model": settings.ANTHROPIC_MODEL},
            {"id": "gpt", "name": "GPT (OpenAI)", "status": "available" if settings.OPENAI_API_KEY else "needs_api_key", "cost": "Free tier", "model": settings.OPENAI_MODEL},
            {"id": "gemini", "name": "Gemini (Google)", "status": "available" if settings.GOOGLE_API_KEY else "needs_api_key", "cost": "Free tier", "model": settings.GEMINI_MODEL},
        ]
    }
