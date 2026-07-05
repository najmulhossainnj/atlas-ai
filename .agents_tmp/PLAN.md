# Implementation Plan: Atlas AI Agent Platform

## 1. OBJECTIVE

Build a production-ready, modular AI agent platform with specialized capabilities for quant research, software engineering, browser automation, and market-making. The goal is to transform the existing foundation into a complete system with async message bus communication, human approval workflows, comprehensive observability, and sandboxed code execution.

## 2. CONTEXT SUMMARY

**Project:** Atlas AI - A Modular Agentic AI Platform  
**Current State:** Foundation exists with core abstractions, but several key components are stubbed or missing.  
**Scale:** Estimated 30,000-80,000 lines for production-ready implementation.

### Existing Components (Solid Foundation)
- ✅ Agent orchestrator (sequential, parallel, hierarchical, collaborative modes)
- ✅ Planning engine (chain of thought, tree of thoughts, recursive decomposition)
- ✅ Memory system (short-term, long-term, semantic, project memory)
- ✅ Tool system base classes and registry
- ✅ Workflow executor with checkpoints
- ✅ LLM factory (OpenAI, Anthropic, Ollama)
- ✅ Plugin SDK and manager
- ✅ Quant module with backtesting
- ✅ FastAPI backend structure
- ✅ Docker deployment configs

### Missing/Gap Components
- ❌ **Message Bus** - No async agent-to-agent communication
- ❌ **Human Approval Layer** - No approval workflow for risky actions
- ❌ **Observability** - No traces, execution replay, structured logging
- ❌ **Sandboxed Execution** - Limited sandboxing for generated code
- ❌ **Tool Implementations** - Only base classes, need actual tools
- ❌ **Frontend Dashboard** - Mentioned in README but not implemented
- ❌ **Persistence Layer** - In-memory only, need PostgreSQL/SQLAlchemy models
- ❌ **Task Queue** - Celery/Arq not integrated
- ❌ **Browser Automation** - Agent exists but no Playwright integration
- ❌ **Vector DB Integration** - Semantic memory needs actual Qdrant/ChromaDB

## 3. APPROACH OVERVIEW

Build incrementally in phases, prioritizing foundational infrastructure before specialized features:

**Phase 1: Core Infrastructure** - Message bus, observability, persistence layer  
**Phase 2: Execution Safety** - Sandboxing, human approval, tool implementations  
**Phase 3: Frontend & Integration** - React dashboard, browser automation, vector DB  
**Phase 4: Specialized Capabilities** - Enhanced quant tools, market-making, risk analysis  

Use plugin architecture throughout to allow optional components and extensibility.

## 4. IMPLEMENTATION STEPS

### Phase 1: Core Infrastructure (Foundation)

#### Step 1.1: Message Bus System
**Goal:** Enable async communication between agents  
**Method:** Implement Redis-based pub/sub event bus

**Files to create:**
- `atlas/core/events/message_bus.py` - Redis pub/sub with fallback
- `atlas/core/events/models.py` - Event message types
- `atlas/core/events/subscribers.py` - Subscription management

#### Step 1.2: Observability Layer
**Goal:** Comprehensive logging, tracing, and execution replay  
**Method:** Integrate OpenTelemetry with structured logging

**Files to create:**
- `atlas/core/telemetry/tracer.py` - OpenTelemetry integration
- `atlas/core/telemetry/logging.py` - Structured logging setup
- `atlas/core/telemetry/execution_replay.py` - Replay store
- `atlas/core/events/message_bus.py` - Add tracing to message bus

#### Step 1.3: Persistence Layer
**Goal:** Database models and SQLAlchemy integration  
**Method:** Define models for agents, tasks, workflows, memory

**Files to create:**
- `atlas/core/models/base.py` - SQLAlchemy async base
- `atlas/core/models/agent.py` - Agent persistence model
- `atlas/core/models/task.py` - Task persistence model
- `atlas/core/models/workflow.py` - Workflow persistence model
- `atlas/core/models/memory.py` - Memory persistence model
- `atlas/core/db/session.py` - Async session management
- `atlas/core/db/migrations.py` - Alembic migrations setup

#### Step 1.4: Task Queue Integration
**Goal:** Background task processing with Arq  
**Method:** Integrate Arq for async task queue

**Files to create:**
- `atlas/core/execution/queue.py` - Arq queue wrapper
- `atlas/core/execution/workers.py` - Worker implementation
- `atlas/core/execution/tasks.py` - Task definitions

---

### Phase 2: Execution Safety

#### Step 2.1: Sandboxed Execution
**Goal:** Run generated code safely in isolation  
**Method:** Docker container + restricted Python execution

**Files to create:**
- `atlas/core/sandbox/container.py` - Docker sandbox manager
- `atlas/core/sandbox/executor.py` - Code execution runner
- `atlas/core/sandbox/restrictions.py` - Resource limits

#### Step 2.2: Human Approval Layer
**Goal:** Require human approval for risky operations  
**Method:** Approval queue with async notification

**Files to create:**
- `atlas/core/approval/manager.py` - Approval workflow engine
- `atlas/core/approval/policies.py` - Risk-based policies
- `atlas/core/approval/notifiers.py` - Webhook/Slack notifications
- `atlas/backend/api/routes/approval.py` - Approval API routes

#### Step 2.3: Tool Implementations
**Goal:** Implement actual tools for filesystem, git, shell, Python  
**Method:** Build on existing base classes

**Files to create/modify:**
- `atlas/core/tools/filesystem.py` - Filesystem operations
- `atlas/core/tools/shell.py` - Shell command execution
- `atlas/core/tools/git.py` - Git operations
- `atlas/core/tools/python_exec.py` - Safe Python execution
- `atlas/core/tools/http.py` - HTTP client with retry
- `atlas/core/tools/builtins.py` - Expand with implementations

---

### Phase 3: Frontend & Integration

#### Step 3.1: React Frontend
**Goal:** Dashboard with chat, workflow builder, memory explorer  
**Method:** Next.js with component library

**Files to create:**
- `atlas/frontend/package.json` - Next.js dependencies
- `atlas/frontend/components/` - UI component library
- `atlas/frontend/pages/` - Next.js pages
- `atlas/frontend/lib/api.ts` - API client

#### Step 3.2: Browser Automation
**Goal:** Full Playwright integration for browser agent  
**Method:** Implement browser tools with Playwright

**Files to create/modify:**
- `atlas/core/tools/browser.py` - Playwright browser tool
- `atlas/modules/browser/module.py` - Browser module expansion

#### Step 3.3: Vector Database Integration
**Goal:** Production-ready semantic memory  
**Method:** Qdrant integration for embeddings

**Files to create/modify:**
- `atlas/core/memory/vector_store.py` - Qdrant wrapper
- `atlas/core/memory/semantic.py` - Rewrite with vector DB
- `atlas/core/embeddings/manager.py` - Embedding generation

---

### Phase 4: Specialized Capabilities

#### Step 4.1: Enhanced Quant Research Module
**Goal:** Full backtesting, factor analysis, portfolio optimization  
**Method:** Expand quant module with additional libraries

**Files to create:**
- `atlas/modules/quant/backtesting.py` - Advanced backtesting engine
- `atlas/modules/quant/factors.py` - Factor library
- `atlas/modules/quant/portfolio.py` - Portfolio optimization
- `atlas/modules/quant/risk_metrics.py` - Risk calculations

#### Step 4.2: Market Making Agent
**Goal:** Production market-making capabilities  
**Method:** Implement order book and exchange interfaces

**Files to create:**
- `atlas/modules/marketmaking/agent.py` - Market making logic
- `atlas/modules/marketmaking/order_book.py` - Order book simulator
- `atlas/modules/marketmaking/quoting.py` - Quote generation
- `atlas/modules/marketmaking/risk.py` - Position risk management

#### Step 4.3: Risk Analysis Agent
**Goal:** Comprehensive risk management  
**Method:** Risk calculation and monitoring

**Files to create:**
- `atlas/modules/risk/calculator.py` - VaR, CVaR calculations
- `atlas/modules/risk/monitor.py` - Real-time monitoring
- `atlas/modules/risk/alerts.py` - Alert system

---

## 5. TESTING AND VALIDATION

### Unit Tests
- Each new module requires unit tests in `tests/unit/`
- Test core components: message bus, tools, workflows

### Integration Tests
- Test agent orchestration end-to-end
- Test message bus communication
- Test workflow execution

### System Tests
- Docker deployment validation
- End-to-end scenarios: quant research workflow, deployment workflow

### Validation Criteria
- All existing tests pass
- New functionality covered by tests
- API endpoints return expected responses
- Frontend loads without errors
- Docker image builds successfully

### Success Metrics
- Agent can execute a multi-step workflow autonomously
- Message bus handles 1000+ events/second
- Sandboxed code execution completes under 30 seconds
- Human approval queue triggers for HIGH risk actions
- Frontend dashboard displays agent status in real-time
