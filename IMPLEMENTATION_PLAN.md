# Atlas AI OS — Implementation Plan

**Generated:** 2026-07-25  
**Status:** Planning  
**Target:** Complete MVP per specification blueprint  

---

## Executive Summary

The Atlas AI OS implementation is currently **~45-50% complete** against the MVP specification. This plan outlines the remaining work organized into 10 phases, prioritizing foundation and MVP completion.

### Current State
- ✅ Core infrastructure (FastAPI, agents, tools, workflows)
- ✅ Database models defined
- ✅ WebSocket streaming
- ✅ Basic frontend UI
- ⚠️ Components are stubs, not production-ready
- ❌ Missing: Manager Agent, Specialist Agents, Skills, Plugins, Migrations

---

## Phase 1: Database & Infrastructure Foundation

**Priority:** P0 (Critical)  
**Estimated Effort:** 2-3 days

### Objectives
- Set up Alembic for database migrations
- Configure Redis for caching and queues
- Create environment configuration system
- Seed initial data

### Tasks

#### 1.1 Alembic Setup
- [ ] Install alembic: `pip install alembic`
- [ ] Initialize alembic in project root
- [ ] Create `alembic.ini` with async PostgreSQL configuration
- [ ] Create `alembic/env.py` with async engine support
- [ ] Create initial migration for all models:
  - [ ] `agents` table
  - [ ] `tasks` table
  - [ ] `workflows` table
  - [ ] `memories` table
  - [ ] `execution_logs` table
  - [ ] `projects` table
- [ ] Create downgrade migrations for all tables

#### 1.2 Redis Integration
- [ ] Create `atlas/core/config.py` with Redis settings
- [ ] Create `atlas/core/cache.py` for Redis caching
- [ ] Create `atlas/core/queue.py` for task queue
- [ ] Add Redis connection pooling
- [ ] Add health check for Redis connectivity

#### 1.3 Environment Configuration
- [ ] Create `.env.example` with all required variables
- [ ] Create `atlas/core/settings.py` using Pydantic Settings
- [ ] Support for: DATABASE_URL, REDIS_URL, API_KEY, etc.
- [ ] Environment-specific configs (dev, staging, prod)

#### 1.4 Database Connection Management
- [ ] Create `atlas/core/db/session.py` for async sessions
- [ ] Create `atlas/core/db/repository.py` base repository class
- [ ] Add connection pooling configuration
- [ ] Add retry logic for connection failures

### Deliverables
- Working database migrations
- Redis caching layer
- Environment configuration system
- Connection management

---

## Phase 2: Manager Agent Core

**Priority:** P0 (Critical)  
**Estimated Effort:** 5-7 days

### Objectives
- Implement the Manager Agent (the "brain" of Atlas)
- Enable goal parsing and task decomposition
- Implement skill matching for agent selection
- Create task delegation system

### Tasks

#### 2.1 Manager Agent Implementation
Create `atlas/core/manager/manager_agent.py`:

```python
class ManagerAgent:
    """Central coordinator for Atlas operations."""
    
    async def process_goal(goal: str) -> ExecutionPlan
    async def decompose_task(task: str) -> list[SubTask]
    async def match_skills(task: SubTask) -> list[Agent]
    async def delegate_task(task: SubTask, agent: Agent) -> TaskResult
    async def review_result(result: TaskResult) -> ReviewResult
```

#### 2.2 Goal Parser
Create `atlas/core/manager/goal_parser.py`:
- [ ] Parse natural language goals
- [ ] Extract requirements and constraints
- [ ] Identify success criteria
- [ ] Handle ambiguous input with clarification prompts

#### 2.3 Task Decomposition
Create `atlas/core/manager/task_decomposer.py`:
- [ ] Break complex goals into subtasks
- [ ] Identify dependencies between tasks
- [ ] Create DAG of task execution order
- [ ] Estimate task complexity and duration

#### 2.4 Skill Matching
Create `atlas/core/manager/skill_matcher.py`:
- [ ] Match task requirements to available skills
- [ ] Rank agents by skill match score
- [ ] Consider agent availability and load
- [ ] Handle skill gaps with recommendations

#### 2.5 Agent Selection
Create `atlas/core/manager/agent_selector.py`:
- [ ] Select optimal agent for each task
- [ ] Consider agent capabilities and current state
- [ ] Implement load balancing
- [ ] Handle agent failures with fallbacks

#### 2.6 Task Delegation
Create `atlas/core/manager/task_delegator.py`:
- [ ] Create task assignments
- [ ] Set task context and constraints
- [ ] Monitor task execution
- [ ] Handle timeouts and retries

### Manager API Endpoints
Create `atlas/backend/api/routes/manager.py`:
- [ ] `POST /api/v1/manager/goal` - Submit a goal
- [ ] `GET /api/v1/manager/plan/{plan_id}` - Get execution plan
- [ ] `GET /api/v1/manager/status/{plan_id}` - Get plan status
- [ ] `POST /api/v1/manager/cancel/{plan_id}` - Cancel execution
- [ ] `POST /api/v1/manager/approve/{task_id}` - Approve human-in-loop tasks

### Deliverables
- Functional Manager Agent
- Goal parsing from natural language
- Automatic task decomposition
- Skill-based agent matching
- Task delegation system

---

## Phase 3: Specialist Agents Implementation

**Priority:** P0 (Critical)  
**Estimated Effort:** 5-7 days

### Objectives
- Implement the MVP specialist agents
- Each agent should be able to execute real tasks
- Agents should use tools and communicate with Manager

### Tasks

#### 3.1 Architect Agent
Create `atlas/agents/architect/agent.py`:
- [ ] Design system architecture from requirements
- [ ] Create component diagrams
- [ ] Define API contracts
- [ ] Specify data models
- [ ] Output: Architecture Design Document

#### 3.2 Backend Developer Agent
Create `atlas/agents/backend/agent.py`:
- [ ] Implement API endpoints from specs
- [ ] Create database models
- [ ] Write unit tests
- [ ] Follow backend best practices
- [ ] Tools: Filesystem, Git, Python, Shell

#### 3.3 Frontend Developer Agent
Create `atlas/agents/frontend/agent.py`:
- [ ] Implement UI components from specs
- [ ] Connect to backend APIs
- [ ] Write frontend tests
- [ ] Ensure accessibility compliance
- [ ] Tools: Filesystem, Git, Node/npm

#### 3.4 Testing Agent
Create `atlas/agents/testing/agent.py`:
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Run test suites
- [ ] Report coverage
- [ ] Create test data/fixtures

#### 3.5 Reviewer Agent
Create `atlas/agents/reviewer/agent.py`:
- [ ] Code review against best practices
- [ ] Security vulnerability scanning
- [ ] Performance analysis
- [ ] Provide improvement suggestions

### Agent Configuration
Create `atlas/agents/config.py`:
```python
AGENT_CONFIGS = {
    "architect": AgentConfig(
        name="Architect",
        role="System Architect",
        goal="Design scalable, maintainable systems",
        skills=["system_design", "api_design", "database_design"],
        tools=["filesystem", "llm"],
    ),
    # ... other agents
}
```

### Deliverables
- 5 functional specialist agents
- Each agent can execute real tasks
- Agents communicate with Manager
- Agents use appropriate tools

---

## Phase 4: Skills System

**Priority:** P1 (High)  
**Estimated Effort:** 3-4 days

### Objectives
- Create skills registry and resolver
- Implement builtin skills
- Enable skill-based agent selection

### Tasks

#### 4.1 Skills Registry
Create `atlas/core/skills/registry.py`:
```python
class SkillRegistry:
    """Central registry for all skills."""
    
    def register(skill: Skill) -> None
    def get(skill_name: str) -> Skill
    def list_skills() -> list[Skill]
    def search_skills(query: str) -> list[Skill]
    def get_by_category(category: str) -> list[Skill]
```

#### 4.2 Skill Model
Create `atlas/core/skills/models.py`:
```python
class Skill(BaseModel):
    name: str
    description: str
    category: str
    capabilities: list[str]
    requirements: list[str]
    cost_estimate: float
    difficulty: Literal["beginner", "intermediate", "advanced", "expert"]
```

#### 4.3 Skill Resolver
Create `atlas/core/skills/resolver.py`:
- [ ] Match task requirements to skills
- [ ] Calculate skill match scores
- [ ] Handle skill dependencies
- [ ] Suggest skill improvements

#### 4.4 Builtin Skills
Create skill modules in `atlas/skills/`:

| Skill | File | Capabilities |
|-------|------|--------------|
| Python | `python.py` | Python programming, debugging, testing |
| FastAPI | `fastapi.py` | REST API design, endpoint implementation |
| React | `react.py` | React component development, state management |
| PostgreSQL | `postgres.py` | Database design, query optimization |
| Docker | `docker.py` | Containerization, docker-compose |
| Git | `git.py` | Version control, branching strategies |
| System Design | `system_design.py` | Scalable architecture design |
| Testing | `testing.py` | Test strategy, pytest, mocking |

#### 4.5 Skill API
Create `atlas/backend/api/routes/skills.py`:
- [ ] `GET /api/v1/skills` - List all skills
- [ ] `GET /api/v1/skills/{name}` - Get skill details
- [ ] `GET /api/v1/skills/search?q=` - Search skills
- [ ] `POST /api/v1/skills` - Register custom skill

### Deliverables
- Skills registry system
- 8 builtin skills implemented
- Skill-based matching in Manager
- Skills API endpoints

---

## Phase 5: Plugin System

**Priority:** P1 (High)  
**Estimated Effort:** 3-4 days

### Objectives
- Enable Atlas extensibility via plugins
- Create plugin manifest format
- Build plugin loader
- Provide plugin SDK

### Tasks

#### 5.1 Plugin Manifest
Create `atlas/core/plugins/manifest.py`:
```python
class PluginManifest(BaseModel):
    name: str
    version: str
    description: str
    author: str
    agents: list[AgentDefinition]
    skills: list[str]
    tools: list[str]
    dependencies: list[str]
```

#### 5.2 Plugin Loader
Create `atlas/core/plugins/loader.py`:
- [ ] Discover plugins from directories
- [ ] Validate plugin manifests
- [ ] Load plugin code safely
- [ ] Manage plugin lifecycle
- [ ] Handle plugin dependencies

#### 5.3 Plugin SDK
Create `atlas/plugins/sdk.py`:
```python
class Plugin:
    """Base class for Atlas plugins."""
    
    manifest: PluginManifest
    agents: list[Agent]
    skills: list[Skill]
    tools: list[Tool]
    
    def install(self) -> None
    def uninstall(self) -> None
    def validate(self) -> bool
```

#### 5.4 Plugin Registry
Create `atlas/core/plugins/registry.py`:
- [ ] Track installed plugins
- [ ] Enable/disable plugins
- [ ] Plugin configuration management
- [ ] Plugin updates

#### 5.5 Plugin API
Create `atlas/backend/api/routes/plugins.py`:
- [ ] `GET /api/v1/plugins` - List plugins
- [ ] `POST /api/v1/plugins/install` - Install plugin
- [ ] `POST /api/v1/plugins/uninstall` - Uninstall plugin
- [ ] `PUT /api/v1/plugins/{name}/enable` - Enable plugin
- [ ] `PUT /api/v1/plugins/{name}/disable` - Disable plugin

### Plugin Examples
Create reference plugins:
- `atlas/plugins/examples/coding.py` - Coding assistance
- `atlas/plugins/examples/research.py` - Web research

### Deliverables
- Plugin manifest format
- Plugin loader
- Plugin SDK
- Plugin API
- 2 example plugins

---

## Phase 6: Frontend IDE Enhancements

**Priority:** P1 (High)  
**Estimated Effort:** 5-7 days

### Objectives
- Add Monaco Editor for code editing
- Create in-browser terminal
- Implement diff viewer
- Build repository explorer

### Tasks

#### 6.1 Monaco Editor Integration
Update `atlas/frontend/src/components/code-editor.tsx`:
- [ ] Install Monaco: `npm install @monaco-editor/react`
- [ ] Create CodeEditor component with syntax highlighting
- [ ] Support for: Python, TypeScript, JavaScript, JSON, YAML, Markdown
- [ ] Theme: Dark mode matching Atlas UI
- [ ] IntelliSense for Python and TypeScript

#### 6.2 Terminal Component
Create `atlas/frontend/src/components/terminal.tsx`:
- [ ] Install xterm.js: `npm install @xterm/xterm @xterm/addon-fit`
- [ ] Create Terminal component
- [ ] Connect to backend terminal session via WebSocket
- [ ] Support command history
- [ ] Copy/paste support

#### 6.3 Diff Viewer
Create `atlas/frontend/src/components/diff-viewer.tsx`:
- [ ] Install diff library: `npm install diff`
- [ ] Create DiffViewer component
- [ ] Side-by-side and unified views
- [ ] Syntax highlighting for diffs
- [ ] Line-by-line navigation

#### 6.4 Repository Explorer
Create `atlas/frontend/src/components/repo-explorer.tsx`:
- [ ] File tree component
- [ ] Directory navigation
- [ ] File preview
- [ ] Git status indicators
- [ ] Search within files

#### 6.5 IDE Layout
Update `atlas/frontend/src/app/ide/page.tsx`:
- [ ] Create main IDE layout
- [ ] File explorer sidebar
- [ ] Editor tabs
- [ ] Terminal panel
- [ ] Output panel
- [ ] Agent activity sidebar

### New Frontend Routes
```
/ide - Full IDE view
/editor/{filePath} - File editor
/terminal - Terminal view
/diff - Diff viewer
/explorer - Repository explorer
```

### Deliverables
- Monaco Editor integration
- Working terminal
- Diff viewer
- Repository explorer
- Full IDE layout

---

## Phase 7: Worker System & Background Jobs

**Priority:** P1 (High)  
**Estimated Effort:** 3-4 days

### Objectives
- Set up background job processing
- Enable scheduled workflows
- Implement job monitoring

### Tasks

#### 7.1 Worker Setup
Create `atlas/workers/` directory:
```
atlas/workers/
├── __init__.py
├── main.py          # Worker entry point
├── config.py        # Worker configuration
└── jobs/
    ├── __init__.py
    ├── execution.py # Task execution jobs
    ├── workflow.py  # Workflow runner
    └── scheduler.py # Scheduled tasks
```

#### 7.2 Job Definitions
Create job classes in `atlas/workers/jobs/`:
```python
class ExecuteAgentJob(Job):
    """Execute an agent task."""
    async def run(self, agent_id: str, task: str) -> dict

class RunWorkflowJob(Job):
    """Run a complete workflow."""
    async def run(self, workflow_id: str) -> dict

class CleanupJob(Job):
    """Periodic cleanup of old data."""
    async def run(self) -> dict
```

#### 7.3 Scheduler
Create `atlas/workers/scheduler.py`:
- [ ] Schedule recurring workflows
- [ ] Cron expression support
- [ ] Workflow templates
- [ ] Schedule management API

#### 7.4 Job API
Create `atlas/backend/api/routes/jobs.py`:
- [ ] `GET /api/v1/jobs` - List jobs
- [ ] `POST /api/v1/jobs` - Create job
- [ ] `GET /api/v1/jobs/{id}` - Get job status
- [ ] `DELETE /api/v1/jobs/{id}` - Cancel job

### Deliverables
- Arq worker setup
- Job definitions
- Scheduler with cron support
- Job monitoring API

---

## Phase 8: LLM Router & Provider Abstraction

**Priority:** P1 (High)  
**Estimated Effort:** 2-3 days

### Objectives
- Integrate LiteLLM for provider routing
- Implement cost tracking
- Add model fallback strategies

### Tasks

#### 8.1 LiteLLM Integration
Update `atlas/core/llm/router.py`:
```python
class LLMRouter:
    """Route LLM requests to optimal provider."""
    
    async def complete(prompt: str, **kwargs) -> LLMResponse
    async def stream(prompt: str, **kwargs) -> AsyncIterator
    async def get_cost(prompt: str, model: str) -> float
```

#### 8.2 Provider Configuration
Update `atlas/core/llm/config.py`:
```python
class LLMConfig(BaseModel):
    providers: list[ProviderConfig]
    default_model: str
    fallback_models: list[str]
    cost_limits: CostLimits
    rate_limits: RateLimits
```

#### 8.3 Cost Tracking
Create `atlas/core/llm/cost_tracker.py`:
- [ ] Track token usage per request
- [ ] Aggregate costs by agent/project
- [ ] Budget alerts
- [ ] Cost reports API

#### 8.4 Model Fallbacks
Implement in router:
- [ ] Primary model failure → fallback model
- [ ] Rate limit → wait and retry
- [ ] Context length exceeded → truncate
- [ ] Cost budget exceeded → stop/degrade

### Deliverables
- LiteLLM integration
- Multi-provider routing
- Cost tracking
- Model fallbacks

---

## Phase 9: Auth, RBAC & Rate Limiting

**Priority:** P2 (Medium)  
**Estimated Effort:** 4-5 days

### Objectives
- Implement user authentication
- Add role-based access control
- Set up API rate limiting

### Tasks

#### 9.1 Authentication
Create `atlas/core/auth/`:
```
atlas/core/auth/
├── __init__.py
├── jwt.py        # JWT handling
├── password.py   # Password hashing
├── oauth.py      # OAuth providers
└── session.py    # Session management
```

Implement:
- [ ] JWT token generation/validation
- [ ] Password hashing (bcrypt)
- [ ] OAuth2 support (GitHub, Google)
- [ ] Session management

#### 9.2 User Management
Create `atlas/core/models/user.py`:
```python
class User(Base, UUIDMixin, TimestampMixin):
    email: str
    password_hash: str
    role: UserRole
    is_active: bool
    # OAuth fields
```

Create API:
- [ ] `POST /api/v1/auth/register`
- [ ] `POST /api/v1/auth/login`
- [ ] `POST /api/v1/auth/logout`
- [ ] `POST /api/v1/auth/refresh`
- [ ] `GET /api/v1/auth/me`

#### 9.3 RBAC Implementation
Create `atlas/core/auth/rbac.py`:
```python
class RBAC:
    """Role-Based Access Control."""
    
    ADMIN = ["*"]  # All permissions
    MANAGER = ["read", "write", "execute", "approve"]
    DEVELOPER = ["read", "write"]
    VIEWER = ["read"]
    VIEWER = ["read"]
```

Apply to routes:
- [ ] Decorator: `@require_permission("write")`
- [ ] Permission checks in API endpoints
- [ ] Resource-level permissions

#### 9.4 Rate Limiting
Create `atlas/core/rate_limit.py`:
- [ ] Redis-based rate limiting
- [ ] Per-user and per-IP limits
- [ ] Configurable limits per endpoint
- [ ] Rate limit headers

### Deliverables
- JWT authentication
- User management API
- RBAC system
- Rate limiting

---

## Phase 10: Testing & Documentation

**Priority:** P2 (Medium)  
**Estimated Effort:** 3-4 days

### Objectives
- Comprehensive unit tests
- Integration tests
- API documentation
- Deployment guides

### Tasks

#### 10.1 Unit Tests
Create `tests/unit/` coverage:
```
tests/unit/
├── test_agents.py      # Agent tests
├── test_manager.py     # Manager tests
├── test_tools.py       # Tool tests
├── test_skills.py      # Skills tests
├── test_memory.py      # Memory tests
├── test_workflow.py    # Workflow tests
└── test_api/           # API tests
    ├── test_agents.py
    ├── test_workflows.py
    └── test_auth.py
```

#### 10.2 Integration Tests
Create `tests/integration/`:
```
tests/integration/
├── test_agent_execution.py
├── test_workflow_execution.py
├── test_manager_delegation.py
└── test_end_to_end.py
```

#### 10.3 API Documentation
Update/create OpenAPI specs:
- [ ] All endpoints documented
- [ ] Request/response examples
- [ ] Error codes documented
- [ ] Authentication requirements

Generate docs with:
```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/openapi.json
```

#### 10.4 Deployment Documentation
Create `docs/`:
```
docs/
├── deployment/
│   ├── docker.md
│   ├── kubernetes.md
│   └── cloud.md
├── development.md
├── configuration.md
├── api-reference.md
└── architecture.md
```

### Deliverables
- 80%+ test coverage
- Integration test suite
- API documentation
- Deployment guides

---

## Implementation Order

### Recommended Sequence

```
Phase 1 (Foundation)
    ↓
Phase 2 (Manager Agent) ← P0 Critical
    ↓
Phase 3 (Specialist Agents) ← P0 Critical
    ↓
Phase 4 (Skills System)
    ↓
Phase 5 (Plugin System)
    ↓
Phase 6 (Frontend IDE)
    ↓
Phase 7 (Workers)
    ↓
Phase 8 (LLM Router)
    ↓
Phase 9 (Auth/RBAC)
    ↓
Phase 10 (Testing/Docs)
```

### Alternative: Parallel Tracks

**Track A (Backend Core):** Phase 1 → 2 → 3 → 4 → 7 → 8  
**Track B (Frontend):** Phase 6 → 4 → 5  
**Track C (Infrastructure):** Phase 9 → 10

---

## Resource Requirements

### Team Composition
- **2-3 Backend Engineers** - Phases 1-5, 7-8
- **1 Frontend Engineer** - Phase 6
- **1 DevOps Engineer** - Phase 9, deployment
- **1 QA Engineer** - Phase 10

### Timeline Estimate
- **With 3 engineers:** 6-8 weeks
- **With 5 engineers:** 4-5 weeks
- **Solo:** 12-16 weeks

---

## Success Metrics

| Metric | Target |
|--------|--------|
| MVP Test Coverage | ≥80% |
| API Documentation | 100% endpoints |
| Frontend Component Tests | ≥70% |
| All phases complete | Phase 1-10 |
| End-to-end demo | Working |

---

## Appendix: File Structure

Target structure after completion:

```
atlas-ai/
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── agents.py
│   │       ├── workflows.py
│   │       ├── manager.py
│   │       ├── skills.py
│   │       ├── plugins.py
│   │       ├── jobs.py
│   │       └── auth.py
│   └── worker/
│       ├── main.py
│       └── jobs/
├── atlas/
│   ├── core/
│   │   ├── agents/
│   │   ├── manager/
│   │   ├── skills/
│   │   ├── tools/
│   │   ├── memory/
│   │   ├── workflow/
│   │   ├── plugins/
│   │   ├── llm/
│   │   ├── auth/
│   │   ├── rate_limit/
│   │   └── db/
│   ├── modules/
│   └── frontend/
├── agents/
│   ├── architect/
│   ├── backend/
│   ├── frontend/
│   ├── testing/
│   └── reviewer/
├── skills/
│   ├── python/
│   ├── fastapi/
│   ├── react/
│   └── ...
├── plugins/
│   └── examples/
├── workers/
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
```
