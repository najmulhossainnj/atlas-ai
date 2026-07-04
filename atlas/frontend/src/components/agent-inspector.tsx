"""Agent inspector component."""

"use client";

import { useState } from "react";
import { 
  Bot, 
  Plus, 
  Settings, 
  Play, 
  Pause, 
  Trash2,
  Activity,
  MessageSquare,
  Clock,
  Zap,
  DollarSign
} from "lucide-react";

type AgentStatus = "idle" | "planning" | "executing" | "waiting" | "finished" | "error";

interface Agent {
  id: string;
  name: string;
  role: string;
  type: string;
  status: AgentStatus;
  metrics: {
    iterations: number;
    tokens_used: number;
    cost: number;
    tool_calls: number;
    errors: number;
  };
  tools: string[];
  skills: string[];
}

const mockAgents: Agent[] = [
  {
    id: "1",
    name: "Software Engineer",
    role: "Code generation and debugging",
    type: "software_engineer",
    status: "idle",
    metrics: { iterations: 24, tokens_used: 45000, cost: 1.25, tool_calls: 12, errors: 1 },
    tools: ["filesystem", "git", "python"],
    skills: ["code_generation", "debugging", "testing"],
  },
  {
    id: "2",
    name: "Research Agent",
    role: "Web research and analysis",
    type: "research",
    status: "executing",
    metrics: { iterations: 8, tokens_used: 12000, cost: 0.35, tool_calls: 5, errors: 0 },
    tools: ["search", "browser"],
    skills: ["web_search", "data_analysis", "report_generation"],
  },
  {
    id: "3",
    name: "Data Agent",
    role: "Data processing and ETL",
    type: "data",
    status: "idle",
    metrics: { iterations: 15, tokens_used: 28000, cost: 0.82, tool_calls: 8, errors: 0 },
    tools: ["database", "api", "python"],
    skills: ["etl", "analytics", "visualization"],
  },
];

const statusColors: Record<AgentStatus, string> = {
  idle: "text-gray-400 bg-gray-800",
  planning: "text-yellow-400 bg-yellow-900/30",
  executing: "text-green-400 bg-green-900/30",
  waiting: "text-blue-400 bg-blue-900/30",
  finished: "text-purple-400 bg-purple-900/30",
  error: "text-red-400 bg-red-900/30",
};

export function AgentInspector() {
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(mockAgents[0]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleDelete = (id: string) => {
    setAgents(agents.filter((a) => a.id !== id));
    if (selectedAgent?.id === id) {
      setSelectedAgent(null);
    }
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-orange-500/20 rounded-lg">
            <Bot className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Agent Inspector</h1>
            <p className="text-gray-400 text-sm">Manage and monitor your agents</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Agent
        </button>
      </div>

      <div className="flex-1 grid grid-cols-3 gap-6">
        <div className="col-span-1 space-y-3">
          <h3 className="text-sm font-medium text-gray-400 uppercase">Agents</h3>
          {agents.map((agent) => (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(agent)}
              className={`p-4 bg-gray-900 rounded-lg border cursor-pointer transition-all ${
                selectedAgent?.id === agent.id
                  ? "border-orange-500 ring-1 ring-orange-500"
                  : "border-gray-800 hover:border-gray-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-orange-400" />
                  <span className="font-medium">{agent.name}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs ${statusColors[agent.status]}`}>
                  {agent.status}
                </span>
              </div>
              <p className="text-xs text-gray-500">{agent.role}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  {agent.metrics.iterations} runs
                </span>
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  {agent.metrics.tool_calls} tools
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="col-span-2 space-y-6">
          {selectedAgent ? (
            <>
              <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="p-4 bg-orange-500/20 rounded-full">
                      <Bot className="w-8 h-8 text-orange-400" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold">{selectedAgent.name}</h2>
                      <p className="text-gray-400">{selectedAgent.role}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
                      <Play className="w-5 h-5" />
                    </button>
                    <button className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
                      <Pause className="w-5 h-5" />
                    </button>
                    <button className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
                      <Settings className="w-5 h-5" />
                    </button>
                    <button 
                      onClick={() => handleDelete(selectedAgent.id)}
                      className="p-2 bg-red-600/20 hover:bg-red-600/30 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-5 h-5 text-red-400" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4 mb-6">
                  <MetricCard
                    icon={<Activity className="w-4 h-4" />}
                    label="Iterations"
                    value={selectedAgent.metrics.iterations}
                  />
                  <MetricCard
                    icon={<Zap className="w-4 h-4" />}
                    label="Tokens"
                    value={selectedAgent.metrics.tokens_used.toLocaleString()}
                  />
                  <MetricCard
                    icon={<DollarSign className="w-4 h-4" />}
                    label="Cost"
                    value={`$${selectedAgent.metrics.cost.toFixed(2)}`}
                  />
                  <MetricCard
                    icon={<MessageSquare className="w-4 h-4" />}
                    label="Tool Calls"
                    value={selectedAgent.metrics.tool_calls}
                  />
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-3">Tools</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgent.tools.map((tool) => (
                        <span
                          key={tool}
                          className="px-3 py-1 bg-gray-800 rounded-full text-sm"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-3">Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgent.skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
                <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  <ActivityRow
                    action="Completed task: Code review"
                    time="2 min ago"
                    status="success"
                  />
                  <ActivityRow
                    action="Used tool: filesystem.read"
                    time="5 min ago"
                    status="info"
                  />
                  <ActivityRow
                    action="Generated code: utils.py"
                    time="8 min ago"
                    status="info"
                  />
                  <ActivityRow
                    action="Error in tool call"
                    time="12 min ago"
                    status="error"
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center">
              <Bot className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-500">Select an agent to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ 
  icon, 
  label, 
  value 
}: { 
  icon: React.ReactNode; 
  label: string; 
  value: string | number;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center gap-2 text-gray-400 mb-2">
        {icon}
        <span className="text-xs uppercase">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function ActivityRow({ 
  action, 
  time, 
  status 
}: { 
  action: string; 
  time: string; 
  status: "success" | "info" | "error";
}) {
  const statusColors = {
    success: "text-green-400",
    info: "text-blue-400",
    error: "text-red-400",
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-gray-500" />
        <span className="text-sm">{action}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`text-xs ${statusColors[status]}`}>
          {status}
        </span>
        <span className="text-xs text-gray-500">{time}</span>
      </div>
    </div>
  );
}
