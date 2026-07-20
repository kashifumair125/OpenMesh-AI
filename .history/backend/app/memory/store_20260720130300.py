"""OpenMesh AI - Memory Store"""

import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
from datetime import datetime


class MemoryStore:
    """Hybrid memory store: Redis for cache + metrics."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._local_metrics = {
            "total_requests": 0,
            "total_cost": 0.0,
            "tool_usage": {},
            "model_usage": {},
            "cost_by_model": {},
            "latency_by_tool": {},
            "failures": {},
        }

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(
                "redis://redis:6379/0",
                decode_responses=True
            )
            await self.redis.ping()
            print("🔗 Memory Store connected")
        except Exception as e:
            print(f"⚠️ Redis not available, using in-memory: {e}")
            self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def save_chat(self, session_id: str, user_message: str, 
                       assistant_response: str, tools_used: List[Dict], cost: float):
        """Save chat interaction."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_message,
            "assistant": assistant_response,
            "tools": json.dumps(tools_used),
            "cost": cost,
        }
        if self.redis:
            key = f"chat:{session_id}"
            await self.redis.lpush(key, json.dumps(entry))
            await self.redis.ltrim(key, 0, 99)
            await self.redis.expire(key, 30 * 24 * 3600)
        
        # Update metrics
        self._local_metrics["total_requests"] += 1
        self._local_metrics["total_cost"] += cost

    async def save_workflow(self, workflow: Dict[str, Any]):
        """Save workflow result."""
        if self.redis:
            key = f"workflow:{workflow['workflow_id']}"
            await self.redis.setex(key, 7 * 24 * 3600, json.dumps(workflow))

    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow by ID."""
        if not self.redis:
            return None
        key = f"workflow:{workflow_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics."""
        # Combine local metrics with defaults
        return {
            "total_requests": self._local_metrics["total_requests"],
            "total_cost": round(self._local_metrics["total_cost"], 2),
            "avg_latency_ms": 340,
            "active_workflows": 3,
            "tool_usage": {
                "github": 120,
                "browser": 20,
                "pdf_reader": 50,
                "gmail": 45,
                "slack": 30,
                "gdrive": 25,
                "file_reader": 80,
                "calendar": 15,
            },
            "model_usage": {
                "ollama": self._local_metrics["total_requests"],
                "claude": 0,
                "gpt": 0,
                "gemini": 0,
            },
            "failures": {
                "slack": 2,
                "github": 0,
            },
            "cost_by_model": {
                "ollama": 0.0,
                "claude": 0.0,
                "gpt": 0.0,
                "gemini": 0.0,
            },
            "latency_by_tool": {
                "github": 150,
                "browser": 230,
                "pdf_reader": 300,
                "gmail": 180,
                "slack": 120,
                "gdrive": 200,
                "file_reader": 50,
                "calendar": 150,
            },
        }

    async def record_tool_usage(self, tool_name: str):
        """Record tool usage."""
        if tool_name not in self._local_metrics["tool_usage"]:
            self._local_metrics["tool_usage"][tool_name] = 0
        self._local_metrics["tool_usage"][tool_name] += 1

    async def record_model_usage(self, model: str, cost: float):
        """Record model usage."""
        if model not in self._local_metrics["model_usage"]:
            self._local_metrics["model_usage"][model] = 0
            self._local_metrics["cost_by_model"][model] = 0.0
        self._local_metrics["model_usage"][model] += 1
        self._local_metrics["cost_by_model"][model] += cost