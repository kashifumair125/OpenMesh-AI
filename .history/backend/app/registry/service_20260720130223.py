"""OpenMesh AI - Tool Registry Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class ToolRegistry:
    """Tool registry with keyword-based discovery."""

    def __init__(self):
        self._tools: List[Dict] = []
        self._usage_stats: Dict[str, Dict] = {}

    async def initialize(self):
        """Register default tools."""
        self._tools = [
            {
                "id": "github-001",
                "name": "github",
                "description": "Access GitHub repositories, pull requests, issues, and code. Can read repos, create issues, review PRs, and search code.",
                "capabilities": ["read_repo", "search_code", "create_issue", "review_pr"],
                "required_permissions": ["github_read", "github_write"],
                "estimated_cost_per_call": 0.01,
                "avg_latency_ms": 150,
                "health_status": "healthy",
                "tags": ["code", "git", "development", "repository"],
                "usage_count": 120,
            },
            {
                "id": "browser-001",
                "name": "browser",
                "description": "Web browser for searching, scraping, and navigating websites. Can search Google, read web pages, and extract information.",
                "capabilities": ["search", "scrape", "navigate"],
                "required_permissions": ["web_access", "browser_read"],
                "estimated_cost_per_call": 0.05,
                "avg_latency_ms": 230,
                "health_status": "healthy",
                "tags": ["web", "search", "scraping", "internet"],
                "usage_count": 20,
            },
            {
                "id": "gmail-001",
                "name": "gmail",
                "description": "Send and read emails via Gmail. Can compose emails, send to recipients, read inbox, and search emails.",
                "capabilities": ["send_email", "read_inbox", "search_emails"],
                "required_permissions": ["email_send", "email_read"],
                "estimated_cost_per_call": 0.02,
                "avg_latency_ms": 180,
                "health_status": "healthy",
                "tags": ["email", "communication", "gmail"],
                "usage_count": 45,
            },
            {
                "id": "slack-001",
                "name": "slack",
                "description": "Send messages and interact with Slack workspaces. Can post to channels, send DMs, and read messages.",
                "capabilities": ["post_message", "send_dm", "read_channel"],
                "required_permissions": ["slack_write", "slack_read"],
                "estimated_cost_per_call": 0.01,
                "avg_latency_ms": 120,
                "health_status": "degraded",
                "tags": ["chat", "messaging", "slack", "communication"],
                "usage_count": 30,
            },
            {
                "id": "gdrive-001",
                "name": "gdrive",
                "description": "Access Google Drive files and folders. Can read, write, upload, and search files in Google Drive.",
                "capabilities": ["read_file", "write_file", "search_files", "upload"],
                "required_permissions": ["gdrive_read", "gdrive_write"],
                "estimated_cost_per_call": 0.01,
                "avg_latency_ms": 200,
                "health_status": "healthy",
                "tags": ["storage", "files", "google", "drive"],
                "usage_count": 25,
            },
            {
                "id": "pdf-001",
                "name": "pdf_reader",
                "description": "Read and extract text from PDF documents. Can extract text, tables, and metadata from PDF files.",
                "capabilities": ["extract_text", "extract_tables", "get_metadata"],
                "required_permissions": ["file_read"],
                "estimated_cost_per_call": 0.005,
                "avg_latency_ms": 300,
                "health_status": "healthy",
                "tags": ["pdf", "document", "reading", "extraction"],
                "usage_count": 50,
            },
            {
                "id": "file-001",
                "name": "file_reader",
                "description": "Read and write local files. Can read text files, write files, and list directory contents.",
                "capabilities": ["read", "write", "list_dir"],
                "required_permissions": ["file_read", "file_write"],
                "estimated_cost_per_call": 0.001,
                "avg_latency_ms": 50,
                "health_status": "healthy",
                "tags": ["filesystem", "files", "local", "io"],
                "usage_count": 80,
            },
            {
                "id": "calendar-001",
                "name": "calendar",
                "description": "Google Calendar integration. Can create events, read schedule, and find free time slots.",
                "capabilities": ["create_event", "read_schedule", "find_free_time"],
                "required_permissions": ["calendar_read", "calendar_write"],
                "estimated_cost_per_call": 0.01,
                "avg_latency_ms": 150,
                "health_status": "healthy",
                "tags": ["calendar", "scheduling", "google", "time"],
                "usage_count": 15,
            },
        ]
        print(f"✅ Registered {len(self._tools)} tools")

    async def discover(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Discover tools using keyword matching."""
        query_lower = query.lower()
        key_terms = [t for t in query_lower.replace(",", " ").replace(".", " ").split() if len(t) > 2]

        scored = []
        for tool in self._tools:
            score = 0
            tool_text = f"{tool['name']} {tool['description']} {' '.join(tool['tags'])} {' '.join(tool['capabilities'])}".lower()

            for term in key_terms:
                if term in tool['name'].lower():
                    score += 15
                elif term in tool_text:
                    score += 5

            # Special mappings
            if "pdf" in query_lower and "pdf" in tool_text:
                score += 10
            if "email" in query_lower and ("gmail" in tool_text or "mail" in tool_text):
                score += 10
            if any(w in query_lower for w in ["web", "search", "browser", "internet"]) and any(w in tool_text for w in ["browser", "web", "search"]):
                score += 10
            if "file" in query_lower and "file" in tool_text:
                score += 8
            if any(w in query_lower for w in ["github", "git", "code", "repo"]) and any(w in tool_text for w in ["github", "git", "code"]):
                score += 10
            if "slack" in query_lower and "slack" in tool_text:
                score += 10
            if "drive" in query_lower and "drive" in tool_text:
                score += 10
            if "calendar" in query_lower and "calendar" in tool_text:
                score += 10

            if score > 0:
                result = dict(tool)
                result["similarity_score"] = round(min(score / 20, 1.0), 2)
                scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    async def list_all(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return self._tools

    async def get(self, tool_id: str) -> Optional[Dict]:
        """Get a tool by ID."""
        for t in self._tools:
            if t["id"] == tool_id:
                return t
        return None

    async def record_usage(self, tool_name: str, latency_ms: float):
        """Record tool usage for metrics."""
        for tool in self._tools:
            if tool["name"] == tool_name:
                tool["usage_count"] += 1
                # Update rolling average latency
                n = tool["usage_count"]
                tool["avg_latency_ms"] = (tool["avg_latency_ms"] * (n - 1) + latency_ms) / n
                break