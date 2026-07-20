"""OpenMesh AI - Gateway API Models"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"      # FREE - Local
    CLAUDE = "claude"      # Free tier
    GPT = "gpt"            # Free tier
    GEMINI = "gemini"      # Free tier


class TaskType(str, Enum):
    """Types of tasks the planner can handle."""
    CHAT = "chat"
    TOOL_CALL = "tool_call"
    WORKFLOW = "workflow"
    RESEARCH = "research"


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1)
    model_provider: Optional[ModelProvider] = Field(
        default=None, 
        description="Override default model provider"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for memory continuity"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="Specific tools to use (auto-discover if not provided)"
    )


class ToolCall(BaseModel):
    """Represents a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    latency_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    model_used: str
    provider: ModelProvider
    tools_called: List[ToolCall] = []
    cost: float = Field(default=0.0, description="Estimated cost in USD")
    latency_ms: float
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolDiscoveryRequest(BaseModel):
    """Request to discover tools by description."""
    query: str = Field(..., description="Natural language tool description")
    top_k: int = Field(default=5, ge=1, le=20)


class ToolInfo(BaseModel):
    """Tool information from registry."""
    id: str
    name: str
    description: str
    capabilities: List[str]
    required_permissions: List[str]
    estimated_cost_per_call: float
    avg_latency_ms: float
    health_status: str = "healthy"
    last_used: Optional[datetime] = None


class WorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="What the workflow should do")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    model_provider: Optional[ModelProvider] = None


class WorkflowStep(BaseModel):
    """A single step in a workflow."""
    step_number: int
    name: str
    description: str
    agent: str
    tools: List[str]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    cost: float = 0.0
    latency_ms: float = 0.0


class WorkflowResponse(BaseModel):
    """Response for workflow execution."""
    workflow_id: str
    name: str
    status: str
    steps: List[WorkflowStep]
    total_cost: float
    total_latency_ms: float
    created_at: datetime
    completed_at: Optional[datetime] = None


class DashboardMetrics(BaseModel):
    """Dashboard metrics response."""
    total_requests: int
    total_cost: float
    avg_latency_ms: float
    active_workflows: int
    tool_usage: Dict[str, int]
    model_usage: Dict[str, int]
    failures: Dict[str, int]
    cost_by_model: Dict[str, float]
    latency_by_tool: Dict[str, float]
