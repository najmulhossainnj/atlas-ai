"""Main dashboard page."""

"use client";

import { useState } from "react";
import { Dashboard } from "@/components/dashboard";
import { ChatInterface } from "@/components/chat-interface";
import { WorkflowBuilder } from "@/components/workflow-builder";
import { MemoryExplorer } from "@/components/memory-explorer";
import { AgentInspector } from "@/components/agent-inspector";
import { Navbar } from "@/components/navbar";

type TabType = "dashboard" | "chat" | "workflows" | "memory" | "agents";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>("dashboard");

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="flex-1 container mx-auto p-6">
        {activeTab === "dashboard" && <Dashboard />}
        {activeTab === "chat" && <ChatInterface />}
        {activeTab === "workflows" && <WorkflowBuilder />}
        {activeTab === "memory" && <MemoryExplorer />}
        {activeTab === "agents" && <AgentInspector />}
      </main>
    </div>
  );
}
