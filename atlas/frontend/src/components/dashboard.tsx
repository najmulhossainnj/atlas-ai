"""Dashboard component showing system overview."""

"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  Bot, 
  Brain, 
  Cpu, 
  Database, 
  HardDrive,
  Zap,
  Clock
} from "lucide-react";

interface DashboardStats {
  agents: number;
  workflows: { active: number; total: number };
  memory: { shortTerm: number; longTerm: number; semantic: number };
  tools: { total: number; categories: number };
  llm: { requests: number; tokens: number; cost: number };
}

const mockStats: DashboardStats = {
  agents: 5,
  workflows: { active: 2, total: 10 },
  memory: { shortTerm: 156, longTerm: 890, semantic: 234 },
  tools: { total: 8, categories: 6 },
  llm: { requests: 1250, tokens: 520000, cost: 12.50 },
};

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>(mockStats);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Atlas Dashboard</h1>
          <p className="text-gray-400">Monitor your agentic AI platform</p>
        </div>
        <div className="flex items-center gap-2 text-gray-400">
          <Clock className="w-4 h-4" />
          <span>{time.toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Agents"
          value={stats.agents}
          icon={<Bot className="w-6 h-6" />}
          trend="+2 this week"
        />
        <StatCard
          title="Active Workflows"
          value={stats.workflows.active}
          subtitle={`${stats.workflows.total} total`}
          icon={<Activity className="w-6 h-6" />}
        />
        <StatCard
          title="Memory Entries"
          value={stats.memory.shortTerm + stats.memory.longTerm}
          subtitle={`${stats.memory.semantic} semantic`}
          icon={<Database className="w-6 h-6" />}
        />
        <StatCard
          title="API Requests"
          value={stats.llm.requests.toLocaleString()}
          subtitle={`${stats.llm.tokens.toLocaleString()} tokens`}
          icon={<Zap className="w-6 h-6" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="System Resources">
          <div className="space-y-4">
            <ResourceBar label="CPU" value={45} />
            <ResourceBar label="Memory" value={62} />
            <ResourceBar label="Disk" value={34} />
            <ResourceBar label="Network" value={18} />
          </div>
        </Card>

        <Card title="LLM Usage">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Cost</span>
              <span className="text-xl font-semibold">${stats.llm.cost.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Token Usage</span>
              <span className="text-lg">{stats.llm.tokens.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Requests Today</span>
              <span className="text-lg">{stats.llm.requests.toLocaleString()}</span>
            </div>
          </div>
        </Card>

        <Card title="Recent Activity">
          <div className="space-y-3">
            <ActivityItem 
              action="Agent completed task"
              agent="Software Engineer"
              time="2 min ago"
            />
            <ActivityItem 
              action="Workflow finished"
              agent="Data Pipeline"
              time="5 min ago"
            />
            <ActivityItem 
              action="Memory consolidated"
              agent="System"
              time="15 min ago"
            />
            <ActivityItem 
              action="New tool registered"
              agent="Browser Agent"
              time="1 hour ago"
            />
          </div>
        </Card>

        <Card title="Quick Actions">
          <div className="grid grid-cols-2 gap-3">
            <ActionButton icon={<Bot className="w-5 h-5" />} label="New Agent" />
            <ActionButton icon={<Activity className="w-5 h-5" />} label="Run Workflow" />
            <ActionButton icon={<Brain className="w-5 h-5" />} label="Chat" />
            <ActionButton icon={<HardDrive className="w-5 h-5" />} label="Explore Memory" />
          </div>
        </Card>
      </div>
    </div>
  );
}

function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend 
}: { 
  title: string; 
  value: string | number; 
  subtitle?: string;
  icon: React.ReactNode;
  trend?: string;
}) {
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-400 text-sm">{title}</span>
        <div className="text-blue-400">{icon}</div>
      </div>
      <div className="text-3xl font-bold mb-1">{value}</div>
      {subtitle && <div className="text-gray-500 text-sm">{subtitle}</div>}
      {trend && <div className="text-green-400 text-xs mt-1">{trend}</div>}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900 rounded-lg p-5 border border-gray-800">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      {children}
    </div>
  );
}

function ResourceBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div 
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

function ActivityItem({ action, agent, time }: { action: string; agent: string; time: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
      <div>
        <div className="text-sm">{action}</div>
        <div className="text-xs text-gray-500">{agent}</div>
      </div>
      <div className="text-xs text-gray-500">{time}</div>
    </div>
  );
}

function ActionButton({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <button className="flex flex-col items-center gap-2 p-4 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
      <div className="text-blue-400">{icon}</div>
      <span className="text-sm">{label}</span>
    </button>
  );
}
