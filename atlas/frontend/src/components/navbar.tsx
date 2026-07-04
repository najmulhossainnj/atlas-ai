"""Navigation bar component."""

"use client";

import Link from "next/link";
import { Bot, Activity, MessageSquare, Workflow, Database, Settings, Moon, Sun } from "lucide-react";

type TabType = "dashboard" | "chat" | "workflows" | "memory" | "agents";

interface NavbarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
  { id: "dashboard", label: "Dashboard", icon: <Activity className="w-5 h-5" /> },
  { id: "chat", label: "Chat", icon: <MessageSquare className="w-5 h-5" /> },
  { id: "workflows", label: "Workflows", icon: <Workflow className="w-5 h-5" /> },
  { id: "memory", label: "Memory", icon: <Database className="w-5 h-5" /> },
  { id: "agents", label: "Agents", icon: <Bot className="w-5 h-5" /> },
];

export function Navbar({ activeTab, onTabChange }: NavbarProps) {
  return (
    <nav className="border-b border-gray-800 bg-gray-900">
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Bot className="w-6 h-6 text-blue-400" />
              </div>
              <span className="text-xl font-bold">Atlas</span>
            </Link>

            <div className="flex items-center gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? "bg-gray-800 text-white"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`}
                >
                  {tab.icon}
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
              <Sun className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-gray-700">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full" />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
