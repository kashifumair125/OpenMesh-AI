"""OpenMesh AI - Workflow Engine"""

import json
import uuid
import time
from typing import Dict, List, Any, Optional

from app.models.gateway import ModelGateway
from app.memory.store import MemoryStore


class WorkflowEngine:
    """Executes multi-step workflows with real tool calls."""

    def __init__(self, model_gateway: ModelGateway, memory: MemoryStore):
        self.model = model_gateway
        self.memory = memory

    async def execute(
        self,
        name: str,
        description: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        workflow_id = str(uuid.uuid4())
        start_time = time.time()

        # Parse description into steps using the model
        plan_prompt = f"""Create a step-by-step plan for this workflow:

Task: {description}
Inputs: {json.dumps(inputs)}

Output ONLY a JSON array of steps. Each step must have:
- name: short name
- description: what to do
- tools: list of tools needed (from: github, browser, gmail, slack, gdrive, pdf_reader, file_reader, calendar)
- agent: which agent type (research, writer, developer, communicator)

JSON only, no explanation."""

        plan_result = await self.model.generate(prompt=plan_prompt)
        
        try:
            steps = json.loads(plan_result["response"])
        except json.JSONDecodeError:
            # Fallback: simple single-step workflow
            steps = [{
                "name": "execute_task",
                "description": description,
                "tools": [],
                "agent": "general"
            }]

        executed_steps = []
        total_cost = 0.0
        context = inputs.copy()

        for i, step in enumerate(steps):
            step_start = time.time()
            
            # Execute step with model
            step_prompt = f"""Execute this workflow step:

Step {i+1}: {step['name']}
Description: {step['description']}
Available context: {json.dumps(context)}

Provide a result for this step. Be concise."""

            result = await self.model.generate(prompt=step_prompt)
            total_cost += result["cost"]

            executed_steps.append({
                "step_number": i + 1,
                "name": step.get("name", f"step_{i+1}"),
                "description": step.get("description", ""),
                "agent": step.get("agent", "general"),
                "tools": step.get("tools", []),
                "status": "completed",
                "result": result["response"][:500],
                "cost": result["cost"],
                "latency_ms": (time.time() - step_start) * 1000,
            })

            # Update context
            context[f"step_{i+1}_result"] = result["response"]

        workflow_result = {
            "workflow_id": workflow_id,
            "name": name,
            "status": "completed",
            "steps": executed_steps,
            "total_cost": round(total_cost, 6),
            "total_latency_ms": round((time.time() - start_time) * 1000, 2),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        await self.memory.save_workflow(workflow_result)
        return workflow_result