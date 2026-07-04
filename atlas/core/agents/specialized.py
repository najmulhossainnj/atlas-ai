"""Specialized agents for Atlas."""

from __future__ import annotations

import asyncio
from typing import Any

from atlas.core.agents.base import (
    Agent,
    AgentConfig,
    AgentMessage,
    AgentType,
    MessageRole,
)


class LLMAgent(Agent):
    """Generic LLM-powered agent."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config)
        self.llm = llm_client

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Reason about the input using the LLM."""
        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in self.messages:
            if msg.role != MessageRole.TOOL:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"usage": response.get("usage", {})},
        )

    async def execute(self, message: AgentMessage) -> AgentMessage:
        """Execute the agent's task."""
        return await self.think(message)

    def _build_system_prompt(self) -> str:
        """Build the system prompt from agent config."""
        return f"""You are {self.name}, a {self.role}.
        
Goal: {self.config.goal}

Your skills: {', '.join(self.config.skills) if self.config.skills else 'None'}
Available tools: {', '.join(self.config.tools) if self.config.tools else 'None'}

Instructions:
- Work autonomously to accomplish your goal
- Use appropriate tools when needed
- Think step by step
- Reflect on your progress
- Report your findings clearly
"""


class GeneralPlannerAgent(LLMAgent):
    """Agent specialized in task decomposition and planning."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.GENERAL_PLANNER

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Analyze the task and create a structured plan."""
        system_prompt = """You are a General Planner Agent specialized in task decomposition.

Your responsibilities:
- Break down complex tasks into smaller, manageable subtasks
- Identify dependencies between tasks
- Estimate effort and resources needed
- Create execution order
- Monitor progress and adjust plans

When given a task:
1. Understand the end goal
2. Identify major components
3. Break down into atomic subtasks
4. Define dependencies
5. Create a step-by-step execution plan

Output your response as a structured plan with clear steps."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"plan": True, "type": "task_decomposition"},
        )


class ResearchAgent(LLMAgent):
    """Agent specialized in web research and information gathering."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.RESEARCH

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Research the topic and synthesize findings."""
        system_prompt = """You are a Research Agent specialized in information gathering and synthesis.

Your responsibilities:
- Conduct thorough web research
- Review literature and sources
- Verify information accuracy
- Generate comprehensive reports
- Cite sources properly

When researching:
1. Identify key questions to answer
2. Search multiple reliable sources
3. Cross-verify information
4. Synthesize findings
5. Provide citations and references
6. Identify knowledge gaps"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"research": True, "sources": []},
        )


class SoftwareEngineerAgent(LLMAgent):
    """Agent specialized in software development tasks."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.SOFTWARE_ENGINEER

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Analyze requirements and generate code."""
        system_prompt = """You are a Software Engineer Agent specialized in code generation and debugging.

Your responsibilities:
- Write clean, maintainable code
- Refactor existing code
- Debug issues
- Write tests
- Follow best practices
- Document code properly

Guidelines:
- Follow the project's coding standards
- Write self-documenting code
- Include error handling
- Consider edge cases
- Optimize for readability and performance
- Write unit tests for new code"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"code": True, "language": "python"},
        )


class ReviewerAgent(LLMAgent):
    """Agent specialized in code and architecture review."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.REVIEWER

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Review code and provide feedback."""
        system_prompt = """You are a Reviewer Agent specialized in code and architecture review.

Your responsibilities:
- Review code for quality
- Check for security vulnerabilities
- Ensure best practices are followed
- Provide constructive feedback
- Score code quality
- Suggest improvements

Review criteria:
- Correctness
- Security
- Performance
- Readability
- Maintainability
- Test coverage
- Documentation"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"review": True, "score": 0},
        )


class BrowserAgent(LLMAgent):
    """Agent specialized in browser automation."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.BROWSER

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Plan browser automation tasks."""
        system_prompt = """You are a Browser Agent specialized in web automation.

Your responsibilities:
- Navigate websites
- Fill forms
- Extract data
- Take screenshots
- Handle authentication
- Manage downloads

Capabilities:
- Multiple browser tabs
- Form filling
- Screenshot capture
- PDF export
- Cookie management
- File downloads

Always ensure actions are performed safely and legally."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"browser_action": True},
        )


class DataAgent(LLMAgent):
    """Agent specialized in data processing and analytics."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.DATA

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Process and analyze data."""
        system_prompt = """You are a Data Agent specialized in data processing and analytics.

Your responsibilities:
- Process CSV, SQL, and API data
- Perform ETL operations
- Generate analytics
- Create visualizations
- Clean and transform data

Capabilities:
- SQL queries
- CSV manipulation
- API integration
- Statistical analysis
- Data visualization

Always validate data quality and handle missing values."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"data_processing": True},
        )


class DocumentationAgent(LLMAgent):
    """Agent specialized in documentation generation."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.DOCUMENTATION

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Generate documentation."""
        system_prompt = """You are a Documentation Agent specialized in creating clear documentation.

Your responsibilities:
- Write README files
- Generate API documentation
- Create architecture docs
- Maintain changelogs
- Write user guides

Guidelines:
- Use clear, concise language
- Include code examples
- Follow documentation standards
- Keep docs up to date
- Use appropriate formatting"""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"documentation": True},
        )


class DeploymentAgent(LLMAgent):
    """Agent specialized in deployment and infrastructure."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.DEPLOYMENT

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Plan and execute deployments."""
        system_prompt = """You are a Deployment Agent specialized in CI/CD and infrastructure.

Your responsibilities:
- Create Docker configurations
- Set up CI/CD pipelines
- Deploy to cloud platforms
- Manage infrastructure as code
- Monitor deployments

Capabilities:
- Docker/Kubernetes
- AWS, GCP, Azure
- GitHub Actions, GitLab CI
- Terraform, Pulumi
- Monitoring and logging

Always follow security best practices."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"deployment": True},
        )


class QuantResearchAgent(LLMAgent):
    """Agent specialized in quantitative finance research."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.QUANT_RESEARCH

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Conduct quantitative research."""
        system_prompt = """You are a Quant Research Agent specialized in quantitative finance.

Your responsibilities:
- Market research and analysis
- Factor research
- Alpha discovery
- Backtesting strategies
- Portfolio analytics
- Risk assessment

Capabilities:
- Statistical analysis
- Time series analysis
- Machine learning models
- Portfolio optimization
- Risk metrics

Always consider market impact and transaction costs."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"quant_research": True},
        )


class MarketMakingAgent(LLMAgent):
    """Agent specialized in market making strategies."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.MARKET_MAKING

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Develop market making strategies."""
        system_prompt = """You are a Market Making Agent specialized in trading strategies.

Your responsibilities:
- Inventory management
- Quoting logic
- Spread optimization
- Risk monitoring
- Exchange connectivity

Key considerations:
- Bid-ask spread management
- Order book dynamics
- Adverse selection
- Inventory risk
- Regulatory compliance

Always prioritize risk management."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"market_making": True},
        )


class RiskManagementAgent(LLMAgent):
    """Agent specialized in risk management."""

    def __init__(self, config: AgentConfig, llm_client: Any):
        super().__init__(config, llm_client)
        self.config.agent_type = AgentType.RISK_MANAGEMENT

    async def think(self, message: AgentMessage) -> AgentMessage:
        """Analyze and manage risk."""
        system_prompt = """You are a Risk Management Agent specialized in financial risk.

Your responsibilities:
- Exposure analysis
- Position limits
- Stop-loss logic
- Volatility monitoring
- Capital allocation

Risk metrics:
- VaR (Value at Risk)
- CVaR (Conditional VaR)
- Sharpe ratio
- Maximum drawdown
- Position concentration

Always maintain conservative risk parameters."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": message.content})

        response = await self.llm.chat(messages)
        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response.get("content", ""),
            metadata={"risk_management": True},
        )
