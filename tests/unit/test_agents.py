"""Unit tests for the agent system."""

import pytest
from atlas.core.agents.base import Agent, AgentConfig, AgentMessage, AgentType, MessageRole
from atlas.core.agents.specialized import LLMAgent, SoftwareEngineerAgent


class MockLLM:
    """Mock LLM for testing."""
    
    async def chat(self, messages, **kwargs):
        return {
            "content": "This is a mock response",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }


@pytest.fixture
def agent_config():
    """Create a test agent configuration."""
    return AgentConfig(
        name="Test Agent",
        role="Test Role",
        goal="Test Goal",
        agent_type=AgentType.CUSTOM,
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    return MockLLM()


@pytest.mark.asyncio
async def test_agent_creation(agent_config):
    """Test agent creation."""
    class SimpleAgent(Agent):
        async def think(self, message):
            return AgentMessage(content="thought")
        
        async def execute(self, message):
            return AgentMessage(content="result")
    
    agent = SimpleAgent(agent_config)
    
    assert agent.name == "Test Agent"
    assert agent.role == "Test Role"
    assert agent.status.value == "idle"


@pytest.mark.asyncio
async def test_agent_run(agent_config):
    """Test agent execution."""
    class SimpleAgent(Agent):
        async def think(self, message):
            return AgentMessage(content="thinking")
        
        async def execute(self, message):
            return AgentMessage(content=f"executed: {message.content}")
    
    agent = SimpleAgent(agent_config)
    result = await agent.run("test input")
    
    assert result.content == "executed: test input"
    assert agent.status.value == "finished"


@pytest.mark.asyncio
async def test_agent_messages(agent_config):
    """Test agent message management."""
    class SimpleAgent(Agent):
        async def think(self, message):
            return AgentMessage(content="thought")
        
        async def execute(self, message):
            return AgentMessage(content="result")
    
    agent = SimpleAgent(agent_config)
    await agent.run("test input")
    
    messages = agent.get_messages()
    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[1].role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_llm_agent(agent_config, mock_llm):
    """Test LLM agent."""
    agent = LLMAgent(agent_config, mock_llm)
    result = await agent.run("test input")
    
    assert result.content == "This is a mock response"
