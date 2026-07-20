"""OpenMesh AI - Memory Store

Hybrid memory using PostgreSQL for persistence and Redis for caching.
"""

import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config import get_settings


class MemoryStore:
    """Hybrid memory store: PostgreSQL (persistent) + Redis (cache)."""

    def __init__(self):
        self.settings = get_settings()
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        self.redis = redis.from_url(
            self.settings.REDIS_URL,
            decode_responses=True
        )
        print("🔗 Memory Store connected")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def save_chat(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        tools_used: List[Dict],
        cost: float,
    ):
        """Save a chat interaction."""
        key = f"chat:{session_id}"
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_message,
            "assistant": assistant_response,
            "tools": json.dumps(tools_used),
            "cost": cost,
        }
        await self.redis.lpush(key, json.dumps(entry))
        await self.redis.ltrim(key, 0, 99)
        await self.redis.expire(key, 30 * 24 * 3600)

    async def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get chat history for a session."""
        key = f"chat:{session_id}"
        entries = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(e) for e in entries]

    async def save_workflow(self, workflow: Dict[str, Any]):
        """Save a workflow result."""
        key = f"workflow:{workflow['workflow_id']}"
        await self.redis.setex(
            key,
            7 * 24 * 3600,
            json.dumps(workflow)
        )

    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get a workflow by ID."""
        key = f"workflow:{workflow_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics from Redis."""
        return {
            "total_requests": int(await self.redis.get("metrics:requests") or 0),
            "total_cost": float(await self.redis.get("metrics:cost") or 0),
            "avg_latency_ms": float(await self.redis.get("metrics:avg_latency") or 0),
            "active_workflows": int(await self.redis.get("metrics:active_workflows") or 0),
            "tool_usage": json.loads(await self.redis.get("metrics:tool_usage") or "{}"),
            "model_usage": json.loads(await self.redis.get("metrics:model_usage") or "{}"),
            "failures": json.loads(await self.redis.get("metrics:failures") or "{}"),
            "cost_by_model": json.loads(await self.redis.get("metrics:cost_by_model") or "{}"),
            "latency_by_tool": json.loads(await self.redis.get("metrics:latency_by_tool") or "{}"),
        }

    async def increment_metric(self, key: str, value: float = 1):
        """Increment a metric counter."""
        await self.redis.incrbyfloat(f"metrics:{key}", value)
