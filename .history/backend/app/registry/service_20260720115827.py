"""OpenMesh AI - Tool Registry (Minimal - no embeddings)"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class ToolRegistry:
    """Simple keyword-based tool registry (no heavy ML models)."""

    def __init__(self):
        self._tools: List[Dict] = []

    async def initialize(self):
        """Register default tools."""
        self._tools = [
            {"id": "github-001", "name": "github", "description": "Access GitHub repositories, PRs, issues", "capabilities": ["read_repo", "search_code", "create_issue"], "required_permissions": ["github_read", "github_write"], "estimated_cost_per_call": 0.01, "avg_latency_ms": 150, "health_status": "healthy", "tags": ["code", "git", "development"], "usage_count": 120},
            {"id": "browser-001", "name": "browser", "description": "Web browser for searching and scraping", "capabilities": ["search", "scrape", "navigate"], "required_permissions": ["web_access", "browser_read"], "estimated_cost_per_call": 0.05, "avg_latency_ms": 230, "health_status": "healthy", "tags": ["web", "search", "scraping"], "usage_count": 20},
            {"id": "gmail-001", "name": "gmail", "description": "Send and read emails via Gmail", "capabilities": ["send_email", "read_inbox", "search_emails"], "required_permissions": ["email_send", "email_read"], "estimated_cost_per_call": 0.02, "avg_latency_ms": 180, "health_status": "healthy", "tags": ["email", "communication"], "usage_count": 45},
            {"id": "slack-001", "name": "slack", "description": "Send messages and interact with Slack", "capabilities": ["post_message", "send_dm", "read_channel"], "required_permissions": ["slack_write", "slack_read"], "estimated_cost_per_call": 0.01, "avg_latency_ms": 120, "health_status": "degraded", "tags": ["chat", "messaging"], "usage_count": 30},
            {"id": "gdrive-001", "name": "gdrive", "description": "Access Google Drive files and folders", "capabilities": ["read_file", "write_file", "search_files"], "required_permissions": ["gdrive_read", "gdrive_write"], "estimated_cost_per_call": 0.01, "avg_latency_ms": 200, "health_status": "healthy", "tags": ["storage", "files"], "usage_count": 25},
            {"id": "pdf-001", "name": "pdf_reader", "description": "Read and extract text from PDFs", "capabilities": ["extract_text", "extract_tables", "get_metadata"], "required_permissions": ["file_read"], "estimated_cost_per_call": 0.005, "avg_latency_ms": 300, "health_status": "healthy", "tags": ["pdf", "document"], "usage_count": 50},
            {"id": "file-001", "name": "file_reader", "description": "Read and write local files", "capabilities": ["read", "write", "list_dir"], "required_permissions": ["file_read", "file_write"], "estimated_cost_per_call": 0.001, "avg_latency_ms": 50, "health_status": "healthy", "tags": ["filesystem", "local"], "usage_count": 80},
            {"id": "calendar-001", "name": "calendar", "description": "Google Calendar integration", "capabilities": ["create_event", "read_schedule", "find_free_time"], "required_permissions": ["calendar_read", "calendar_write"], "estimated_cost_per_call": 0.01, "avg_latency_ms": 150, "health_status": "healthy", "tags": ["calendar", "scheduling"], "usage_count": 15},
        ]
        print(f"✅ Registered {len(self._tools)} tools")

    async def discover(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword matching for tool discovery."""
        query_lower = query.lower()
        # Extract key terms from query
        key_terms = query_lower.replace("find me", "").replace("tools", "").replace("tool", "").replace("which", "").replace("can", "").replace("to", "").strip().split()

        scored = []
        for tool in self._tools:
            score = 0
            tool_text = f"{tool['name']} {tool['description']} {' '.join(tool['tags'])} {' '.join(tool['capabilities'])}".lower()

            # Check each key term
            for term in key_terms:
                if len(term) < 2:  # Skip single char terms
                    continue
                if term in tool['name'].lower():
                    score += 15
                elif term in tool_text:
                    score += 5
                # Partial matches (e.g., "pdf" matches "pdf_reader")
                elif term in tool_text.replace("_", " "):
                    score += 3

            # Special case: query contains "pdf" and tool is pdf_reader
            if "pdf" in query_lower and "pdf" in tool_text:
                score += 10
            if "email" in query_lower and ("gmail" in tool_text or "mail" in tool_text):
                score += 10
            if "web" in query_lower or "search" in query_lower or "browser" in query_lower:
                if "browser" in tool_text or "web" in tool_text:
                    score += 10
            if "file" in query_lower and "file" in tool_text:
                score += 8
            if "github" in query_lower or "git" in query_lower or "code" in query_lower:
                if "github" in tool_text or "git" in tool_text:
                    score += 10

            if score > 0:
                result = dict(tool)
                result["similarity_score"] = min(score / 20, 1.0)
                scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
    async def list_all(self) -> List[Dict[str, Any]]:
        return self._tools

    async def get(self, tool_id: str) -> Optional[Dict]:
        for t in self._tools:
            if t["id"] == tool_id:
                return t
        return None
