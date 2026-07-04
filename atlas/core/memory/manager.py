"""Memory manager for coordinating different memory systems."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from atlas.core.memory.short_term import ShortTermMemory
from atlas.core.memory.long_term import LongTermMemory
from atlas.core.memory.semantic import SemanticMemory
from atlas.core.memory.project import ProjectMemory


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: str = "short_term"
    project_id: Optional[str] = None
    agent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    importance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None


class MemoryManager:
    """Manages all memory systems and provides unified access."""

    def __init__(
        self,
        short_term_max: int = 1000,
        long_term_max: int = 10000,
        semantic_enabled: bool = True,
        project_memory_enabled: bool = True,
    ):
        self.short_term = ShortTermMemory(max_entries=short_term_max)
        self.long_term = LongTermMemory(max_entries=long_term_max)
        self.semantic = SemanticMemory() if semantic_enabled else None
        self.project_memory: dict[str, ProjectMemory] = {}
        self.project_memory_enabled = project_memory_enabled
        self._lock = asyncio.Lock()

    async def add(
        self,
        content: str,
        memory_type: str = "short_term",
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        importance: float = 1.0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Add a new memory entry."""
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            project_id=project_id,
            agent_id=agent_id,
            importance=importance,
            metadata=metadata or {},
        )

        async with self._lock:
            if memory_type == "short_term":
                await self.short_term.add(entry)
            elif memory_type == "long_term":
                await self.long_term.add(entry)
            elif memory_type == "semantic" and self.semantic:
                entry.embedding = await self.semantic.create_embedding(content)
                await self.semantic.add(entry)
            elif memory_type == "project" and project_id and self.project_memory_enabled:
                if project_id not in self.project_memory:
                    self.project_memory[project_id] = ProjectMemory(project_id)
                await self.project_memory[project_id].add(entry)

        return entry

    async def get(
        self,
        memory_id: str,
        memory_type: Optional[str] = None,
    ) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        async with self._lock:
            if memory_type == "short_term":
                return await self.short_term.get(memory_id)
            elif memory_type == "long_term":
                return await self.long_term.get(memory_id)
            elif memory_type == "semantic" and self.semantic:
                return await self.semantic.get(memory_id)
            elif memory_type == "project":
                for pm in self.project_memory.values():
                    entry = await pm.get(memory_id)
                    if entry:
                        return entry

            for memory in [self.short_term, self.long_term, self.semantic]:
                if memory:
                    entry = await memory.get(memory_id)
                    if entry:
                        return entry

            for pm in self.project_memory.values():
                entry = await pm.get(memory_id)
                if entry:
                    return entry

        return None

    async def search(
        self,
        query: str,
        memory_types: Optional[list[str]] = None,
        limit: int = 10,
        project_id: Optional[str] = None,
    ) -> list[MemoryEntry]:
        """Search memories across different memory systems."""
        results = []

        async with self._lock:
            if memory_types is None or "semantic" in memory_types:
                if self.semantic:
                    semantic_results = await self.semantic.search(query, limit=limit)
                    results.extend(semantic_results)

            if memory_types is None or "project" in memory_types:
                if project_id and project_id in self.project_memory:
                    project_results = await self.project_memory[project_id].search(query)
                    results.extend(project_results[:limit])

            if memory_types is None or "short_term" in memory_types:
                short_results = await self.short_term.search(query)
                results.extend(short_results[:limit])

            if memory_types is None or "long_term" in memory_types:
                long_results = await self.long_term.search(query)
                results.extend(long_results[:limit])

        results.sort(key=lambda x: x.importance * x.access_count, reverse=True)
        return results[:limit]

    async def recall(
        self,
        context: str,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Recall relevant memories based on context."""
        if self.semantic:
            return await self.semantic.search(context, limit=limit)
        return []

    async def forget(
        self,
        memory_id: str,
        memory_type: Optional[str] = None,
    ) -> bool:
        """Remove a memory entry."""
        async with self._lock:
            if memory_type == "short_term":
                return await self.short_term.remove(memory_id)
            elif memory_type == "long_term":
                return await self.long_term.remove(memory_id)
            elif memory_type == "semantic" and self.semantic:
                return await self.semantic.remove(memory_id)
            elif memory_type == "project":
                for pm in self.project_memory.values():
                    if await pm.remove(memory_id):
                        return True
                return False

            for memory in [self.short_term, self.long_term, self.semantic]:
                if memory and await memory.remove(memory_id):
                    return True

            return False

    async def consolidate(self) -> int:
        """Consolidate short-term memories into long-term storage."""
        consolidated = 0
        
        async with self._lock:
            to_consolidate = await self.short_term.get_important_entries(
                threshold=0.7
            )
            
            for entry in to_consolidate:
                entry.memory_type = "long_term"
                await self.long_term.add(entry)
                await self.short_term.remove(entry.id)
                consolidated += 1

            if self.semantic:
                for entry in to_consolidate:
                    entry.embedding = await self.semantic.create_embedding(entry.content)
                    await self.semantic.add(entry)

        return consolidated

    async def clear(
        self,
        memory_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """Clear memory stores."""
        async with self._lock:
            if memory_type is None or memory_type == "short_term":
                await self.short_term.clear()
            
            if memory_type is None or memory_type == "long_term":
                await self.long_term.clear()
            
            if (memory_type is None or memory_type == "semantic") and self.semantic:
                await self.semantic.clear()
            
            if project_id and project_id in self.project_memory:
                await self.project_memory[project_id].clear()

    async def get_stats(self) -> dict[str, Any]:
        """Get statistics about memory usage."""
        return {
            "short_term": await self.short_term.get_stats(),
            "long_term": await self.long_term.get_stats(),
            "semantic": await self.semantic.get_stats() if self.semantic else None,
            "projects": len(self.project_memory),
            "project_memory": {
                pid: await pm.get_stats()
                for pid, pm in self.project_memory.items()
            } if self.project_memory else {},
        }

    async def export_memory(
        self,
        memory_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Export memories for backup or transfer."""
        data = {"exported_at": datetime.utcnow().isoformat()}

        if memory_type is None or memory_type == "short_term":
            data["short_term"] = await self.short_term.export()

        if memory_type is None or memory_type == "long_term":
            data["long_term"] = await self.long_term.export()

        if (memory_type is None or memory_type == "semantic") and self.semantic:
            data["semantic"] = await self.semantic.export()

        if project_id and project_id in self.project_memory:
            data["project"] = await self.project_memory[project_id].export()

        return data

    async def import_memory(
        self,
        data: dict[str, Any],
        overwrite: bool = False,
    ) -> int:
        """Import memories from backup."""
        imported = 0

        if "short_term" in data:
            for entry_data in data["short_term"]:
                entry = MemoryEntry(**entry_data)
                await self.short_term.add(entry)
                imported += 1

        if "long_term" in data:
            for entry_data in data["long_term"]:
                entry = MemoryEntry(**entry_data)
                await self.long_term.add(entry)
                imported += 1

        if "semantic" in data and self.semantic:
            for entry_data in data["semantic"]:
                entry = MemoryEntry(**entry_data)
                await self.semantic.add(entry)
                imported += 1

        return imported
