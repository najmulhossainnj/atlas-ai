"""Workflow builder component."""

"use client";

import { useState } from "react";
import { 
  Plus, 
  Play, 
  Pause, 
  Trash2, 
  GripVertical,
  ChevronRight,
  Settings,
  Workflow as WorkflowIcon
} from "lucide-react";

interface Step {
  id: string;
  name: string;
  type: "task" | "condition" | "loop" | "parallel";
  config: Record<string, unknown>;
  children: Step[];
}

const initialWorkflow: Step[] = [
  {
    id: "1",
    name: "Start",
    type: "task",
    config: {},
    children: [],
  },
  {
    id: "2",
    name: "Process Data",
    type: "task",
    config: { handler: "data_processor" },
    children: [],
  },
  {
    id: "3",
    name: "Send Notification",
    type: "task",
    config: { handler: "notifier" },
    children: [],
  },
];

export function WorkflowBuilder() {
  const [workflowName, setWorkflowName] = useState("My Workflow");
  const [steps, setSteps] = useState<Step[]>(initialWorkflow);
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleAddStep = () => {
    const newStep: Step = {
      id: Date.now().toString(),
      name: `New Step ${steps.length + 1}`,
      type: "task",
      config: {},
      children: [],
    };
    setSteps([...steps, newStep]);
  };

  const handleDeleteStep = (id: string) => {
    setSteps(steps.filter((s) => s.id !== id));
    if (selectedStep === id) {
      setSelectedStep(null);
    }
  };

  const handleToggleRun = () => {
    setIsRunning(!isRunning);
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/20 rounded-lg">
            <WorkflowIcon className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="text-2xl font-bold bg-transparent border-none outline-none"
            />
            <p className="text-gray-400 text-sm">Workflow Builder</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleAddStep}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Step
          </button>
          <button
            onClick={handleToggleRun}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              isRunning
                ? "bg-yellow-600 hover:bg-yellow-700"
                : "bg-green-600 hover:bg-green-700"
            }`}
          >
            {isRunning ? (
              <>
                <Pause className="w-4 h-4" />
                Pause
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-gray-900 rounded-lg border border-gray-800 p-6 overflow-auto">
          <h3 className="text-lg font-semibold mb-4">Workflow Steps</h3>
          <div className="space-y-2">
            {steps.map((step, index) => (
              <div key={step.id}>
                <div
                  className={`flex items-center gap-3 p-4 bg-gray-800 rounded-lg cursor-pointer transition-colors ${
                    selectedStep === step.id ? "ring-2 ring-blue-500" : ""
                  }`}
                  onClick={() => setSelectedStep(step.id)}
                >
                  <GripVertical className="w-4 h-4 text-gray-500 cursor-grab" />
                  <div className="flex-1">
                    <div className="font-medium">{step.name}</div>
                    <div className="text-xs text-gray-500 uppercase">{step.type}</div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteStep(step.id);
                    }}
                    className="p-2 hover:bg-gray-700 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-gray-400" />
                  </button>
                  <Settings className="w-4 h-4 text-gray-500" />
                </div>
                {index < steps.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ChevronRight className="w-4 h-4 text-gray-600 rotate-90" />
                  </div>
                )}
              </div>
            ))}
          </div>
          {steps.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <p>No steps yet. Click "Add Step" to start building your workflow.</p>
            </div>
          )}
        </div>

        <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h3 className="text-lg font-semibold mb-4">Step Configuration</h3>
          {selectedStep ? (
            <StepConfig step={steps.find((s) => s.id === selectedStep)} />
          ) : (
            <p className="text-gray-500">Select a step to configure</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StepConfig({ step }: { step?: Step }) {
  if (!step) return null;

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm text-gray-400 mb-1">Name</label>
        <input
          type="text"
          defaultValue={step.name}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
        />
      </div>
      <div>
        <label className="block text-sm text-gray-400 mb-1">Type</label>
        <select
          defaultValue={step.type}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
        >
          <option value="task">Task</option>
          <option value="condition">Condition</option>
          <option value="loop">Loop</option>
          <option value="parallel">Parallel</option>
        </select>
      </div>
      <div>
        <label className="block text-sm text-gray-400 mb-1">Handler</label>
        <input
          type="text"
          placeholder="handler_name"
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500"
        />
      </div>
      <div>
        <label className="block text-sm text-gray-400 mb-1">Timeout (seconds)</label>
        <input
          type="number"
          defaultValue={3600}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
        />
      </div>
      <div>
        <label className="block text-sm text-gray-400 mb-1">Retries</label>
        <input
          type="number"
          defaultValue={3}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
        />
      </div>
    </div>
  );
}
