"""Unit tests for the memory system."""

import pytest
from atlas.core.memory.manager import MemoryManager, MemoryEntry
from atlas.core.memory.short_term import ShortTermMemory
from atlas.core.memory.long_term import LongTermMemory


@pytest.mark.asyncio
async def test_memory_manager_creation():
    """Test memory manager creation."""
    manager = MemoryManager()
    assert manager is not None


@pytest.mark.asyncio
async def test_add_memory():
    """Test adding a memory entry."""
    manager = MemoryManager()
    entry = await manager.add(
        content="Test memory content",
        memory_type="short_term",
        importance=0.8,
    )
    
    assert entry is not None
    assert entry.content == "Test memory content"
    assert entry.importance == 0.8


@pytest.mark.asyncio
async def test_search_memory():
    """Test searching memories."""
    manager = MemoryManager()
    
    await manager.add(content="Python programming", memory_type="short_term")
    await manager.add(content="JavaScript frameworks", memory_type="short_term")
    await manager.add(content="Python web development", memory_type="short_term")
    
    results = await manager.search("Python")
    assert len(results) >= 2


@pytest.mark.asyncio
async def test_short_term_memory():
    """Test short-term memory."""
    memory = ShortTermMemory(max_entries=10)
    
    entry = MemoryEntry(content="test", memory_type="short_term")
    await memory.add(entry)
    
    retrieved = await memory.get(entry.id)
    assert retrieved is not None
    assert retrieved.content == "test"


@pytest.mark.asyncio
async def test_short_term_eviction():
    """Test LRU eviction in short-term memory."""
    memory = ShortTermMemory(max_entries=3)
    
    for i in range(5):
        entry = MemoryEntry(content=f"entry {i}", memory_type="short_term")
        await memory.add(entry)
    
    stats = memory.get_stats()
    assert stats["total_entries"] <= 3
