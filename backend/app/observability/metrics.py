"""OpenMesh AI - Simple Metrics (no prometheus dependency)"""

from fastapi import FastAPI

# Simple in-memory counters (no external dependencies)
_request_count = 0
_total_cost = 0.0
_tool_usage = {}
_model_usage = {}


def setup_metrics(app: FastAPI):
    """Setup minimal metrics - no heavy dependencies."""

    @app.get("/metrics")
    async def metrics():
        return {
            "total_requests": _request_count,
            "total_cost": _total_cost,
            "tool_usage": _tool_usage,
            "model_usage": _model_usage,
        }

    from starlette.middleware.base import BaseHTTPMiddleware
    import time

    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            global _request_count
            _request_count += 1
            start = time.time()
            response = await call_next(request)
            return response

    app.add_middleware(MetricsMiddleware)
