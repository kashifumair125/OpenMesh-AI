# OpenMesh AI - Universal AI Tool Operating System

> Dynamic tool discovery, sandboxed execution, multi-agent orchestration — built for the 2026 AI engineering job market.

## Architecture

```
User → Web UI (Next.js) → OpenMesh AI Gateway (FastAPI)
                                    ↓
                           Planner Agent (LangGraph)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
                 Claude           GPT            Gemini
                    ↓               ↓               ↓
               MCP Client      MCP Client      MCP Client
                    └───────────────┼───────────────┘
                                    ↓
                           Tool Registry
                                    ↓
                           Sandbox Layer (Docker)
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
               Permissions    Cost Tracking    Memory
                    └───────────────┼───────────────┘
                                    ↓
                           Observability Dashboard
```

## Features

- **Dynamic Tool Discovery**: Semantic search over tool registry — "Find me PDF tools" → auto-selects best tools
- **Permission Engine**: Docker-like policies per agent — Claude can read files but not delete them
- **Multi-Model Gateway**: Route to Ollama (free), Claude, GPT, or Gemini with cost-aware routing
- **Workflow Builder**: Multi-step workflows with LangGraph — Resume → Find Jobs → Tailor → Send
- **Observability Dashboard**: Real-time cost tracking, latency metrics, failure rates
- **Zero-Cost Development**: Runs entirely on local Ollama + free API tiers

## Quick Start (Zero Cost)

### 1. Clone & Setup
```bash
git clone <your-repo>
cd openmesh-ai
```

### 2. Start Infrastructure
```bash
cd backend/docker
docker-compose up -d postgres redis ollama
```

### 3. Pull Free Local Model
```bash
docker exec -it openmesh-ai-ollama-1 ollama pull phi3:3.8b
```

### 4. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Backend runs at: http://localhost:8000
API Docs: http://localhost:8000/docs

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, Recharts, ReactFlow |
| Backend | FastAPI, Pydantic, Uvicorn |
| AI | LangGraph, LangChain, Ollama |
| MCP | Model Context Protocol SDK |
| Database | PostgreSQL + pgvector, Redis |
| Sandbox | Docker + seccomp |
| Monitoring | Prometheus, OpenTelemetry |
| Deployment | Docker Compose, Kubernetes |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/chat` | Main chat with tool discovery |
| `POST /api/v1/tools/discover` | Semantic tool search |
| `GET /api/v1/tools` | List all tools |
| `POST /api/v1/workflows` | Execute multi-step workflow |
| `GET /api/v1/dashboard/metrics` | Real-time metrics |
| `GET /api/v1/models` | List available models |

## Zero-Cost Model Strategy

| Provider | Cost | Setup |
|----------|------|-------|
| **Ollama** (default) | $0 | Local, runs on your machine |
| Claude | Free tier (~$5) | Set `ANTHROPIC_API_KEY` |
| GPT | Free tier ($5-$18) | Set `OPENAI_API_KEY` |
| Gemini | Free tier (1500/day) | Set `GOOGLE_API_KEY` |

All models use the same unified gateway interface. Swap providers by changing one parameter.

## Project Structure

```
openmesh-ai/
├── frontend/           # Next.js 14 + Tailwind
│   ├── app/           # Pages (chat, workflows, tools, dashboard)
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── gateway/   # FastAPI routes
│   │   ├── planner/   # LangGraph agent
│   │   ├── registry/  # Tool discovery (semantic search)
│   │   ├── sandbox/   # Docker sandbox + permissions
│   │   ├── models/    # LLM gateway (Ollama/Claude/GPT/Gemini)
│   │   ├── observability/  # Metrics, tracing, cost tracking
│   │   └── memory/    # Redis + PostgreSQL storage
│   ├── docker/        # Docker Compose + K8s manifests
│   └── requirements.txt
└── README.md
```

## Why This Gets You Hired

1. **Production Architecture**: Not a tutorial — real multi-service system
2. **Security Mindset**: Permission engine + sandboxing (rare in portfolios)
3. **Cost Awareness**: Built-in cost tracking shows business thinking
4. **Observability**: Dashboard with real metrics = production experience
5. **MCP Protocol**: Cutting-edge Model Context Protocol adoption
6. **Multi-Agent**: LangGraph orchestration = in-demand skill

## License

MIT
