"""OpenMesh AI - Planner Agent State"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class PlannerState(TypedDict):
    """State managed by the LangGraph planner."""

    # Input
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    session_id: str

    # Planning
    intent: Optional[str]
    required_tools: List[str]
    selected_tools: List[Dict[str, Any]]

    # Execution
    tool_results: List[Dict[str, Any]]
    current_step: int

    # Output
    response: Optional[str]
    model_used: Optional[str]
    provider: Optional[str]
    cost: float
    tools_called: List[Dict[str, Any]]

    # Control
    next_step: Optional[str]
    error: Optional[str]
