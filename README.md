# Atlas - A Modular Agentic AI Platform

A production-quality, extensible, open agentic AI platform written primarily in Python.

## Vision

Build a reusable operating system for AI agents that can autonomously solve complex tasks by planning, reasoning, collaborating, using tools, remembering information, and learning from previous executions.

## Features

- **Multi-Agent System**: General Planner, Research, Software Engineer, Reviewer, Browser, Data, Documentation, Deployment, Quant Research, Market Making, and Risk Management agents
- **Planning Engine**: Chain of Thought, Tree of Thoughts, Graph planning, Recursive decomposition, Reflection, Replanning
- **Memory System**: Short-term, Long-term, Semantic memory with vector embeddings
- **Tool System**: Plugin-based with built-in tools for filesystem, git, terminal, python, search
- **Workflow Engine**: Sequential, Parallel, Conditional, Loop workflows with retries and checkpoints
- **LLM Layer**: Provider agnostic with OpenAI, Anthropic, Ollama support
- **Backend API**: FastAPI with REST endpoints and WebSocket
- **Frontend Dashboard**: React/Next.js with chat, workflow builder, memory explorer

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                               │
│   React/Next.js Dashboard - Chat, Workflow Builder, etc.    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                             │
│   FastAPI - REST, WebSocket, Auth, Rate Limiting           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Core Engine   │   │  Modules      │   │   Plugins     │
│               │   │               │   │               │
│ • Agent System│   │ • Coding      │   │ • Custom      │
│ • Memory      │   │ • Browser     │   │   Agents      │
│ • Tools       │   │ • Quant       │   │ • Custom      │
│ • Planning    │   │               │   │   Tools       │
│ • Workflow    │   │               │   │               │
│ • LLM Layer   │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Installation

```bash
# Clone the repository
git clone https://github.com/najmulhossainnj/atlas-ai.git
cd atlas-ai

# Install dependencies
pip install -e .

# Or install with extras
pip install -e ".[all]"  # All dependencies
pip install -e ".[dev]"   # Development dependencies
```

## Quick Start

```python
from atlas import AgentOrchestrator, AgentConfig, AgentType

# Create an orchestrator
orchestrator = AgentOrchestrator(mode="sequential")

# Create and register an agent
config = AgentConfig(
    name="My Agent",
    role="Assistant",
    goal="Help users with their tasks",
    agent_type=AgentType.CUSTOM,
)
agent = LLMAgent(config, llm_client)
await orchestrator.register_agent(agent)

# Run the agent
result = await agent.run("Hello, how can you help me?")
print(result.content)
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=atlas tests/

# Format code
ruff format .

# Lint code
ruff check .
```

## Deployment

### Docker

```bash
cd deployments/docker
docker-compose up -d
```

### Kubernetes

```bash
cd deployments/kubernetes
kubectl apply -f .
```

## License

MIT License
