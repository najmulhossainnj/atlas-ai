"""Memory explorer component."""

"use client";

import { useState } from "react";
import { 
  Search, 
  Database, 
  Brain, 
  Clock,
  Filter,
  Trash2,
  Download,
  Upload,
  Plus
} from "lucide-react";

type MemoryType = "all" | "short_term" | "long_term" | "semantic" | "project";

interface MemoryEntry {
  id: string;
  content: string;
  type: MemoryType;
  importance: number;
  created_at: string;
  accessed_at: string;
}

const mockMemories: MemoryEntry[] = [
  {
    id: "1",
    content: "User prefers dark mode interface",
    type: "long_term",
    importance: 0.9,
    created_at: "2024-01-15T10:30:00Z",
    accessed_at: "2024-01-20T14:00:00Z",
  },
  {
    id: "2",
    content: "Current project context: building a dashboard",
    type: "project",
    importance: 0.8,
    created_at: "2024-01-20T09:00:00Z",
    accessed_at: "2024-01-20T15:30:00Z",
  },
  {
    id: "3",
    content: "Code review feedback on API endpoints",
    type: "semantic",
    importance: 0.7,
    created_at: "2024-01-19T11:00:00Z",
    accessed_at: "2024-01-19T16:00:00Z",
  },
  {
    id: "4",
    content: "Recent chat about authentication",
    type: "short_term",
    importance: 0.5,
    created_at: "2024-01-20T14:30:00Z",
    accessed_at: "2024-01-20T14:45:00Z",
  },
];

export function MemoryExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<MemoryType>("all");
  const [memories, setMemories] = useState<MemoryEntry[]>(mockMemories);

  const filteredMemories = memories.filter((memory) => {
    const matchesSearch = memory.content.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = activeFilter === "all" || memory.type === activeFilter;
    return matchesSearch && matchesFilter;
  });

  const handleDelete = (id: string) => {
    setMemories(memories.filter((m) => m.id !== id));
  };

  const typeColors: Record<MemoryType, string> = {
    all: "text-gray-400",
    short_term: "text-yellow-400",
    long_term: "text-green-400",
    semantic: "text-purple-400",
    project: "text-blue-400",
  };

  const typeLabels: Record<MemoryType, string> = {
    all: "All",
    short_term: "Short-term",
    long_term: "Long-term",
    semantic: "Semantic",
    project: "Project",
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-green-500/20 rounded-lg">
            <Brain className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Memory Explorer</h1>
            <p className="text-gray-400 text-sm">Explore and manage agent memories</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
        <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-1">
          {(Object.keys(typeLabels) as MemoryType[]).map((type) => (
            <button
              key={type}
              onClick={() => setActiveFilter(type)}
              className={`px-3 py-2 rounded-md text-sm transition-colors ${
                activeFilter === type
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {typeLabels[type]}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <span className="text-gray-400">{filteredMemories.length} memories</span>
            <button className="flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded-lg text-sm transition-colors">
              <Plus className="w-4 h-4" />
              Add Memory
            </button>
          </div>
          <div className="overflow-auto max-h-[calc(100%-60px)]">
            {filteredMemories.map((memory) => (
              <div
                key={memory.id}
                className="p-4 border-b border-gray-800 hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs font-medium uppercase ${typeColors[memory.type]}`}>
                        {typeLabels[memory.type]}
                      </span>
                      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden w-24">
                        <div
                          className={`h-full ${
                            memory.type === "short_term" ? "bg-yellow-500" :
                            memory.type === "long_term" ? "bg-green-500" :
                            memory.type === "semantic" ? "bg-purple-500" :
                            "bg-blue-500"
                          }`}
                          style={{ width: `${memory.importance * 100}%` }}
                        />
                      </div>
                    </div>
                    <p className="text-gray-200 mb-2">{memory.content}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(memory.created_at).toLocaleDateString()}
                      </span>
                      <span>Accessed {new Date(memory.accessed_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(memory.id)}
                    className="p-2 hover:bg-gray-700 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            ))}
            {filteredMemories.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No memories found</p>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
            <h3 className="text-lg font-semibold mb-4">Memory Statistics</h3>
            <div className="space-y-3">
              <StatRow label="Short-term" value={12} color="text-yellow-400" />
              <StatRow label="Long-term" value={89} color="text-green-400" />
              <StatRow label="Semantic" value={156} color="text-purple-400" />
              <StatRow label="Project" value={24} color="text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
            <h3 className="text-lg font-semibold mb-4">Actions</h3>
            <div className="space-y-2">
              <ActionButton 
                icon={<Brain className="w-4 h-4" />} 
                label="Consolidate Memory"
                description="Move important short-term to long-term"
              />
              <ActionButton 
                icon={<Filter className="w-4 h-4" />} 
                label="Clean Old Memories"
                description="Remove memories older than 30 days"
              />
              <ActionButton 
                icon={<Database className="w-4 h-4" />} 
                label="Optimize Semantic Index"
                description="Rebuild similarity index"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className={`font-semibold ${color}`}>{value}</span>
    </div>
  );
}

function ActionButton({ 
  icon, 
  label, 
  description 
}: { 
  icon: React.ReactNode; 
  label: string; 
  description: string;
}) {
  return (
    <button className="w-full text-left p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
      <div className="flex items-center gap-3 mb-1">
        <div className="text-blue-400">{icon}</div>
        <span className="font-medium">{label}</span>
      </div>
      <p className="text-xs text-gray-500 ml-9">{description}</p>
    </button>
  );
}
