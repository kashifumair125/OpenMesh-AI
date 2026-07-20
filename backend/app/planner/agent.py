"""OpenMesh AI - Planner Agent (Minimal)

The brain of OpenMesh AI. Uses LangGraph to:
1. Understand user intent
2. Discover and select tools
3. Build execution plans
4. Orchestrate multi-step workflows
"""

import json
import uuid
import time
from typing import Dict, List, Any, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.planner.state import PlannerState
from app.planner.workflows import get_workflow_template
from app.models.gateway import ModelGateway
from app.registry.service import ToolRegistry
from app.memory.store import MemoryStore


SYSTEM_PROMPT = """You are the Planner Agent for OpenMesh AI, a universal AI tool operating system.

Your job is to:
1. Understand what the user wants
2. Determine which tools are needed
3. Plan the execution steps
4. Delegate to appropriate models and tools

Available tool categories:
- github: Code repositories, PRs, issues
- browser: Web search, scraping
- gmail: Email sending/reading
- slack: Messaging
- gdrive: File storage
- pdf_reader: Document reading
- file_reader: Local file access
- calendar: Scheduling

When responding, output valid JSON with this structure:
{
    "intent": "description of what user wants",
    "requires_tools": true/false,
    "tools_needed": ["tool1", "tool2"],
    "plan": ["step 1", "step 2"],
    "can_handle_directly": true/false
}
"""


class PlannerAgent:
    """LangGraph-based planner agent."""

    def __init__(
        self,
        model_gateway: ModelGateway,
        registry: ToolRegistry,
        memory: MemoryStore,
    ):
        self.model = model_gateway
        self.registry = registry
        self.memory = memory
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(PlannerState)

        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("discover_tools", self._discover_tools)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("handle_error", self._handle_error)

        workflow.set_entry_point("understand_intent")
        workflow.add_edge("understand_intent", "discover_tools")
        workflow.add_edge("discover_tools", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def _understand_intent(self, state: PlannerState) -> PlannerState:
        """Node: Understand what the user wants."""
        prompt = f"""Analyze this user request and determine the plan:

User: {state['user_input']}

Respond with JSON only."""

        result = await self.model.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT
        )

        try:
            plan_data = json.loads(result["response"])
            state["intent"] = plan_data.get("intent", "general_chat")
            state["required_tools"] = plan_data.get("tools_needed", [])
            state["next_step"] = "discover_tools" if plan_data.get("requires_tools") else "generate_response"
            state["cost"] += result["cost"]
            state["model_used"] = result["model_used"]
            state["provider"] = result["provider"]
        except json.JSONDecodeError:
            state["intent"] = "general_chat"
            state["required_tools"] = []
            state["next_step"] = "generate_response"

        return state

    async def _discover_tools(self, state: PlannerState) -> PlannerState:
        """Node: Discover tools from the registry."""
        if not state["required_tools"]:
            return state

        selected_tools = []
        for tool_name in state["required_tools"]:
            tools = await self.registry.discover(query=tool_name, top_k=3)
            if tools:
                selected_tools.extend(tools)

        state["selected_tools"] = selected_tools
        return state

    async def _execute_tools(self, state: PlannerState) -> PlannerState:
        """Node: Execute discovered tools."""
        if not state["selected_tools"]:
            return state

        tool_results = []
        tools_called = []

        for tool in state["selected_tools"]:
            tool_name = tool["name"]

            start = time.time()
            try:
                result = await self._execute_mcp_tool(tool_name, state["user_input"])
                latency = (time.time() - start) * 1000

                tool_results.append({
                    "tool": tool_name,
                    "result": result,
                    "latency_ms": latency
                })
                tools_called.append({
                    "tool_name": tool_name,
                    "arguments": {"query": state["user_input"]},
                    "result": str(result)[:500],
                    "latency_ms": latency,
                    "success": True,
                    "error": None
                })
            except Exception as e:
                tools_called.append({
                    "tool_name": tool_name,
                    "arguments": {},
                    "result": None,
                    "success": False,
                    "error": str(e)
                })

        state["tool_results"] = tool_results
        state["tools_called"] = tools_called
        return state

    async def _execute_mcp_tool(self, tool_name: str, query: str) -> Any:
        """Execute an MCP tool (mock implementation)."""
        mock_results = {
            "github": {"repos": ["openmesh-ai", "langgraph", "mcp"], "status": "ok"},
            "browser": {"results": f"Search results for: {query}", "status": "ok"},
            "gmail": {"sent": True, "message_id": "mock-123"},
            "slack": {"posted": True, "channel": "#general"},
            "gdrive": {"files": ["resume.pdf", "cover_letter.docx"]},
            "pdf_reader": {"text": "Extracted PDF content...", "pages": 2},
            "file_reader": {"content": "File contents..."},
            "calendar": {"events": ["Meeting at 2pm"]},
        }
        return mock_results.get(tool_name, {"status": "unknown_tool"})

    async def _generate_response(self, state: PlannerState) -> PlannerState:
        """Node: Generate final response to user."""
        tool_context = ""
        if state["tool_results"]:
            tool_context = "\n\nTool Results:\n" + json.dumps(state["tool_results"], indent=2)

        prompt = f"""User: {state['user_input']}

{tool_context}

Provide a helpful response based on the tool results. If no tools were used, answer directly."""

        result = await self.model.generate(prompt=prompt)

        state["response"] = result["response"]
        state["cost"] += result["cost"]
        state["model_used"] = result["model_used"]
        state["provider"] = result["provider"]

        return state

    async def _handle_error(self, state: PlannerState) -> PlannerState:
        """Node: Handle errors gracefully."""
        state["response"] = f"I encountered an error: {state.get('error', 'Unknown error')}. Please try again."
        state["error"] = None
        return state

    async def execute(
        self,
        message: str,
        session_id: str,
        requested_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a user request through the planner."""
        initial_state: PlannerState = {
            "messages": [HumanMessage(content=message)],
            "user_input": message,
            "session_id": session_id,
            "intent": None,
            "required_tools": requested_tools or [],
            "selected_tools": [],
            "tool_results": [],
            "current_step": 0,
            "response": None,
            "model_used": None,
            "provider": None,
            "cost": 0.0,
            "tools_called": [],
            "next_step": None,
            "error": None,
        }

        final_state = await self.graph.ainvoke(initial_state)

        await self.memory.save_chat(
            session_id=session_id,
            user_message=message,
            assistant_response=final_state["response"],
            tools_used=final_state["tools_called"],
            cost=final_state["cost"]
        )

        return {
            "response": final_state["response"],
            "model_used": final_state["model_used"],
            "provider": final_state["provider"],
            "tools_called": final_state["tools_called"],
            "cost": round(final_state["cost"], 6),
        }

    async def execute_workflow(
        self,
        name: str,
        description: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a predefined multi-step workflow."""
        workflow_id = str(uuid.uuid4())

        try:
            steps = get_workflow_template(name)
        except ValueError:
            steps = await self._generate_workflow_steps(description)

        executed_steps = []
        total_cost = 0.0
        total_latency = 0.0
        context = inputs.copy()

        for step in steps:
            step_start = time.time()

            step_prompt = f"""Execute this workflow step:

Step: {step['name']}
Description: {step['description']}
Context: {json.dumps(context)}

Perform the task and return the result."""

            result = await self.model.generate(prompt=step_prompt)
            total_cost += result["cost"]

            step_latency = (time.time() - step_start) * 1000
            total_latency += step_latency

            executed_steps.append({
                "step_number": step["step"],
                "name": step["name"],
                "description": step["description"],
                "agent": step["agent"],
                "tools": step["tools"],
                "status": "completed",
                "result": result["response"][:500],
                "cost": result["cost"],
                "latency_ms": step_latency,
            })

            output_key = step.get("output_key", f"step_{step['step']}_result")
            context[output_key] = result["response"]

        workflow_result = {
            "workflow_id": workflow_id,
            "name": name,
            "status": "completed",
            "steps": executed_steps,
            "total_cost": round(total_cost, 6),
            "total_latency_ms": round(total_latency, 2),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        await self.memory.save_workflow(workflow_result)

        return workflow_result

    async def _generate_workflow_steps(self, description: str) -> List[Dict[str, Any]]:
        """Dynamically generate workflow steps from description."""
        prompt = f"""Generate a workflow plan for this task:

Task: {description}

Output a JSON array of steps, each with:
- step: number
- name: short name
- description: what to do
- agent: which agent type (research, writer, developer, communicator, memory)
- tools: list of tools needed
- input_keys: what data it needs
- output_key: what data it produces

JSON only."""

        result = await self.model.generate(prompt=prompt)
        try:
            return json.loads(result["response"])
        except json.JSONDecodeError:
            return [{
                "step": 1,
                "name": "execute_task",
                "description": description,
                "agent": "general",
                "tools": [],
                "input_keys": [],
                "output_key": "result"
            }]
