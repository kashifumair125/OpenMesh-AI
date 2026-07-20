"use client";

import { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Workflow,
  Wrench,
  BarChart3,
  Shield,
  Cpu,
  DollarSign,
  Clock,
  AlertTriangle,
  CheckCircle,
  Zap,
  GitBranch,
  Globe,
  Mail,
  MessageCircle,
  FileText,
  Calendar,
  HardDrive,
  Send,
  Loader2,
  Bot,
  User,
  ChevronRight,
  Activity,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

// Types
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  model?: string;
  tools?: ToolCall[];
  cost?: number;
  latency?: number;
}

interface ToolCall {
  tool_name: string;
  success: boolean;
  latency_ms: number;
}

interface ToolInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  health_status: string;
  usage_count: number;
}

interface DashboardMetrics {
  total_requests: number;
  total_cost: number;
  avg_latency_ms: number;
  tool_usage: Record<string, number>;
  model_usage: Record<string, number>;
  cost_by_model: Record<string, number>;
  latency_by_tool: Record<string, number>;
}

interface WorkflowStep {
  step_number: number;
  name: string;
  description: string;
  agent: string;
  tools: string[];
  status: string;
  result?: string;
  cost: number;
  latency_ms: number;
}

interface WorkflowResult {
  workflow_id: string;
  name: string;
  status: string;
  steps: WorkflowStep[];
  total_cost: number;
  total_latency_ms: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const mockMetrics: DashboardMetrics = {
  total_requests: 1247,
  total_cost: 2.34,
  avg_latency_ms: 340,
  tool_usage: { github: 120, browser: 20, pdf_reader: 50, gmail: 45, slack: 30, gdrive: 25, file_reader: 80, calendar: 15 },
  model_usage: { ollama: 800, claude: 200, gpt: 150, gemini: 97 },
  cost_by_model: { ollama: 0, claude: 1.25, gpt: 0.75, gemini: 0.34 },
  latency_by_tool: { github: 150, browser: 230, pdf_reader: 300, gmail: 180, slack: 120, gdrive: 200, file_reader: 50, calendar: 150 },
};

const costData = [
  { name: "Claude", cost: 1.25, fill: "#E57035" },
  { name: "GPT", cost: 0.75, fill: "#10A37F" },
  { name: "Gemini", cost: 0.34, fill: "#4285F4" },
  { name: "Ollama", cost: 0, fill: "#FF6B6B" },
];

const latencyData = [
  { name: "GitHub", latency: 150 },
  { name: "Browser", latency: 230 },
  { name: "PDF", latency: 300 },
  { name: "Gmail", latency: 180 },
  { name: "Slack", latency: 120 },
  { name: "Drive", latency: 200 },
];

export default function Dashboard() {
  // Chat state
  const [activeTab, setActiveTab] = useState<"chat" | "workflows" | "tools" | "dashboard">("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Welcome to OpenMesh AI! I'm your universal tool orchestrator. I can discover tools dynamically, execute them in sandboxes, and manage multi-step workflows. Try asking me to find tools or execute a workflow.",
      model: "Ollama/phi3:3.8b",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("ollama");

  // Tools state
  const [tools, setTools] = useState<ToolInfo[]>([]);

  // Workflow state
  const [customWorkflow, setCustomWorkflow] = useState("");
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<WorkflowResult | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState("");

  // Dashboard state
  const [metrics, setMetrics] = useState<DashboardMetrics>(mockMetrics);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/tools`);
      if (res.ok) {
        const data = await res.json();
        setTools(data);
      }
    } catch {
      setTools([
        { id: "1", name: "github", description: "GitHub repository access", capabilities: ["read_repo", "search_code"], health_status: "healthy", usage_count: 120 },
        { id: "2", name: "browser", description: "Web browsing and search", capabilities: ["search", "scrape"], health_status: "healthy", usage_count: 20 },
        { id: "3", name: "gmail", description: "Email management", capabilities: ["send_email", "read_inbox"], health_status: "healthy", usage_count: 45 },
        { id: "4", name: "slack", description: "Slack messaging", capabilities: ["post_message", "send_dm"], health_status: "degraded", usage_count: 30 },
        { id: "5", name: "gdrive", description: "Google Drive access", capabilities: ["read_file", "write_file"], health_status: "healthy", usage_count: 25 },
        { id: "6", name: "pdf_reader", description: "PDF document reading", capabilities: ["extract_text", "extract_tables"], health_status: "healthy", usage_count: 50 },
        { id: "7", name: "file_reader", description: "Read and write local files", capabilities: ["read", "write", "list_dir"], health_status: "healthy", usage_count: 80 },
        { id: "8", name: "calendar", description: "Google Calendar integration", capabilities: ["create_event", "read_schedule"], health_status: "healthy", usage_count: 15 },
      ]);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          model_provider: selectedModel,
          session_id: "demo-session",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.response,
            model: data.model_used,
            tools: data.tools_called,
            cost: data.cost,
            latency: data.latency_ms,
          },
        ]);
      } else {
        const error = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${error.detail || "Something went wrong"}`,
            model: selectedModel,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Backend connection failed. Make sure the server is running on localhost:8000",
          model: "error",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const runWorkflow = async (name: string, description: string) => {
    if (!description.trim()) return;
    
    setWorkflowLoading(true);
    setSelectedWorkflow(name);
    setWorkflowResult(null);
    
    try {
      const res = await fetch(`${API_URL}/api/v1/workflows`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          inputs: { query: description },
          model_provider: selectedModel,
        }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setWorkflowResult(data);
      } else {
        const error = await res.json();
        console.error("Workflow failed:", error);
      }
    } catch (e) {
      console.error("Workflow failed:", e);
    } finally {
      setWorkflowLoading(false);
      setSelectedWorkflow("");
    }
  };

  const getToolIcon = (name: string) => {
    const icons: Record<string, any> = {
      github: GitBranch,
      browser: Globe,
      gmail: Mail,
      slack: MessageCircle,
      gdrive: HardDrive,
      pdf_reader: FileText,
      file_reader: FileText,
      calendar: Calendar,
    };
    return icons[name] || Wrench;
  };

  const getHealthColor = (status: string) => {
    if (status === "healthy") return "text-emerald-400 bg-emerald-400/10";
    if (status === "degraded") return "text-amber-400 bg-amber-400/10";
    return "text-red-400 bg-red-400/10";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight">OpenMesh AI</h1>
              <p className="text-xs text-slate-400">Universal Tool OS</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <button
            onClick={() => setActiveTab("chat")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Chat
          </button>
          <button
            onClick={() => setActiveTab("workflows")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "workflows"
                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Workflow className="w-4 h-4" />
            Workflows
          </button>
          <button
            onClick={() => setActiveTab("tools")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "tools"
                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Wrench className="w-4 h-4" />
            Tool Registry
          </button>
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "dashboard"
                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Dashboard
          </button>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-800/50">
            <Shield className="w-4 h-4 text-emerald-400" />
            <div className="flex-1">
              <p className="text-xs font-medium text-slate-200">Sandbox Active</p>
              <p className="text-xs text-slate-500">Docker isolation enabled</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            {activeTab === "chat" && (
              <>
                <Cpu className="w-4 h-4 text-slate-400" />
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ollama">🦙 Ollama (Free)</option>
                  <option value="claude">🟠 Claude</option>
                  <option value="gpt">🟢 GPT</option>
                  <option value="gemini">🔵 Gemini</option>
                </select>
                <span className="text-xs text-slate-500">
                  {selectedModel === "ollama" ? "Local • $0.00" : "Cloud • Metered"}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <DollarSign className="w-3 h-3 text-emerald-400" />
              <span className="text-xs font-medium text-emerald-400">${metrics.total_cost.toFixed(2)}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <Activity className="w-3 h-3 text-blue-400" />
              <span className="text-xs font-medium text-blue-400">{metrics.total_requests} reqs</span>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          {/* CHAT TAB */}
          {activeTab === "chat" && (
            <div className="flex flex-col h-full">
              <div className="flex-1 overflow-auto p-6 space-y-6">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-4 ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {msg.role === "assistant" && (
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                    )}
                    <div
                      className={`max-w-2xl rounded-2xl px-5 py-4 ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-slate-800 border border-slate-700"
                      }`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      {msg.role === "assistant" && msg.tools && msg.tools.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-700 space-y-2">
                          {msg.tools.map((tool, ti) => (
                            <div key={ti} className="flex items-center gap-2 text-xs">
                              {tool.success ? (
                                <CheckCircle className="w-3 h-3 text-emerald-400" />
                              ) : (
                                <AlertTriangle className="w-3 h-3 text-red-400" />
                              )}
                              <span className="text-slate-400">{tool.tool_name}</span>
                              <span className="text-slate-500">{tool.latency_ms}ms</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {msg.role === "assistant" && (msg.cost !== undefined || msg.latency) && (
                        <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                          <span>{msg.model}</span>
                          {msg.cost !== undefined && <span>${msg.cost.toFixed(4)}</span>}
                          {msg.latency && <span>{msg.latency}ms</span>}
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-slate-300" />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              <div className="border-t border-slate-800 p-4">
                <div className="max-w-3xl mx-auto flex gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Ask OpenMesh AI anything..."
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-5 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={isLoading}
                    className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded-xl text-white transition-colors flex items-center gap-2"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-center text-xs text-slate-600 mt-2">
                  Tools are sandboxed • Permissions enforced • Costs tracked
                </p>
              </div>
            </div>
          )}

          {/* WORKFLOWS TAB */}
          {activeTab === "workflows" && (
            <div className="p-6">
              <h2 className="text-2xl font-bold mb-6">Workflow Builder</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                {[
                  { name: "Job Application", description: "Resume → Find Jobs → Tailor → Send → Track", steps: 5, icon: FileText, color: "from-blue-500 to-cyan-500" },
                  { name: "Code Review", description: "PR → Analyze → Review → Comment", steps: 4, icon: GitBranch, color: "from-violet-500 to-purple-500" },
                  { name: "Research Report", description: "Topic → Search → Synthesize → Report", steps: 4, icon: Globe, color: "from-emerald-500 to-teal-500" },
                ].map((workflow) => (
                  <button
                    key={workflow.name}
                    onClick={() => runWorkflow(workflow.name, workflow.description)}
                    disabled={workflowLoading}
                    className="group relative p-6 rounded-2xl bg-slate-800/50 border border-slate-700 hover:border-slate-500 transition-all text-left hover:bg-slate-800 disabled:opacity-50"
                  >
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${workflow.color} flex items-center justify-center mb-4`}>
                      <workflow.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-lg mb-1">{workflow.name}</h3>
                    <p className="text-sm text-slate-400 mb-4">{workflow.description}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <Workflow className="w-3 h-3" />
                      <span>{workflow.steps} steps</span>
                    </div>
                    {workflowLoading && selectedWorkflow === workflow.name && (
                      <Loader2 className="absolute right-4 top-4 w-5 h-5 animate-spin text-blue-400" />
                    )}
                  </button>
                ))}
              </div>

              <div className="p-6 rounded-2xl bg-slate-800/30 border border-dashed border-slate-700">
                <h3 className="font-semibold mb-2">Custom Workflow</h3>
                <p className="text-sm text-slate-400 mb-4">
                  Describe what you want to automate, and the Planner Agent will generate and execute a workflow.
                </p>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={customWorkflow}
                    onChange={(e) => setCustomWorkflow(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && runWorkflow("Custom", customWorkflow)}
                    placeholder="e.g., 'Research Tesla stock, write summary, email it to me'"
                    className="flex-1 bg-slate-800 border border-slate-700