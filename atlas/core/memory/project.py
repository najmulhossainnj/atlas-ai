"""Project-specific memory storage."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from atlas.core.memory.manager import MemoryEntry


class ProjectMemoryType(str, Enum):
    """Types of project memory."""
    DOCUMENT = "document"
    CODE = "code"
    CONVERSATION = "conversation"
    ARCHITECTURE = "architecture"
    EXECUTION_HISTORY = "execution_history"
    ARTIFACT = "artifact"


@dataclass
class ProjectMemoryEntry:
    """A memory entry within a project context."""
    id: str
    content: str
    memory_type: ProjectMemoryType = ProjectMemoryType.DOCUMENT
    file_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProjectMemory:
    """Memory system for a specific project."""

    def __init__(self, project_id: str, storage_path: Optional[str] = None):
        self.project_id = project_id
        self.storage_path = storage_path
        self._entries: dict[str, ProjectMemoryEntry] = {}
        self._by_type: dict[ProjectMemoryType, list[str]] = {t: [] for t in ProjectMemoryType}
        self._by_file: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the project memory store."""
        if self._initialized:
            return
        
        if self.storage_path:
            await self._load_from_disk()
        
        self._initialized = True

    async def add(
        self,
        entry: "MemoryEntry",
        memory_type: ProjectMemoryType = ProjectMemoryType.DOCUMENT,
    ) -> ProjectMemoryEntry:
        """Add a new entry to project memory."""
        await self.initialize()
        
        project_entry = ProjectMemoryEntry(
            id=entry.id,
            content=entry.content,
            memory_type=memory_type,
            metadata=entry.metadata,
        )
        
        if entry.metadata.get("file_path"):
            project_entry.file_path = entry.metadata["file_path"]
        
        if entry.metadata.get("tags"):
            project_entry.tags = entry.metadata["tags"]
        
        async with self._lock:
            self._entries[project_entry.id] = project_entry
            self._by_type[memory_type].append(project_entry.id)
            
            if project_entry.file_path:
                self._by_file[project_entry.file_path] = project_entry.id
        
        if self.storage_path:
            await self._save_entry(project_entry)
        
        return project_entry

    async def get(self, entry_id: str) -> Optional[ProjectMemoryEntry]:
        """Retrieve a project memory entry."""
        await self.initialize()
        
        async with self._lock:
            return self._entries.get(entry_id)

    async def get_by_file(self, file_path: str) -> Optional[ProjectMemoryEntry]:
        """Get memory entry associated with a file."""
        await self.initialize()
        
        async with self._lock:
            entry_id = self._by_file.get(file_path)
            if entry_id:
                return self._entries.get(entry_id)
        return None

    async def get_by_type(
        self,
        memory_type: ProjectMemoryType,
        limit: int = 100,
    ) -> list[ProjectMemoryEntry]:
        """Get all entries of a specific type."""
        await self.initialize()
        
        async with self._lock:
            entry_ids = self._by_type.get(memory_type, [])
            entries = []
            
            for entry_id in entry_ids[-limit:]:
                entry = self._entries.get(entry_id)
                if entry:
                    entries.append(entry)
            
            return entries

    async def search(
        self,
        query: str,
        memory_types: Optional[list[ProjectMemoryType]] = None,
        limit: int = 20,
    ) -> list[ProjectMemoryEntry]:
        """Search project memory."""
        await self.initialize()
        
        async with self._lock:
            results = []
            query_lower = query.lower()
            
            types_to_search = memory_types or list(ProjectMemoryType)
            
            for memory_type in types_to_search:
                entry_ids = self._by_type.get(memory_type, [])
                
                for entry_id in entry_ids:
                    entry = self._entries.get(entry_id)
                    if entry:
                        if (query_lower in entry.content.lower() or
                            query_lower in " ".join(entry.tags).lower()):
                            results.append(entry)
            
            results.sort(key=lambda x: x.updated_at, reverse=True)
            return results[:limit]

    async def update(
        self,
        entry_id: str,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[ProjectMemoryEntry]:
        """Update an existing entry."""
        await self.initialize()
        
        async with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return None
            
            if content is not None:
                entry.content = content
                entry.version += 1
            
            if tags is not None:
                entry.tags = tags
            
            if metadata is not None:
                entry.metadata.update(metadata)
            
            entry.updated_at = datetime.utcnow()
            
            if self.storage_path:
                await self._save_entry(entry)
            
            return entry

    async def remove(self, entry_id: str) -> bool:
        """Remove an entry from project memory."""
        await self.initialize()
        
        async with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return False
            
            self._entries.pop(entry_id)
            self._by_type[entry.memory_type].remove(entry_id)
            
            if entry.file_path:
                self._by_file.pop(entry.file_path, None)
            
            return True

    async def clear(self) -> None:
        """Clear all project memory."""
        async with self._lock:
            self._entries.clear()
            for entry_list in self._by_type.values():
                entry_list.clear()
            self._by_file.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about project memory."""
        return {
            "project_id": self.project_id,
            "total_entries": len(self._entries),
            "by_type": {
                t.value: len(ids) for t, ids in self._by_type.items()
            },
        }

    async def export(self) -> dict[str, Any]:
        """Export project memory."""
        await self.initialize()
        
        async with self._lock:
            return {
                "project_id": self.project_id,
                "exported_at": datetime.utcnow().isoformat(),
                "entries": [
                    {
                        "id": e.id,
                        "content": e.content,
                        "memory_type": e.memory_type.value,
                        "file_path": e.file_path,
                        "created_at": e.created_at.isoformat(),
                        "updated_at": e.updated_at.isoformat(),
                        "version": e.version,
                        "tags": e.tags,
                        "metadata": e.metadata,
                    }
                    for e in self._entries.values()
                ],
            }

    async def _save_entry(self, entry: ProjectMemoryEntry) -> None:
        """Save an entry to disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        import os
        
        entry_dir = f"{self.storage_path}/projects/{self.project_id}"
        os.makedirs(entry_dir, exist_ok=True)
        
        entry_file = f"{entry_dir}/{entry.id}.json"
        async with aiofiles.open(entry_file, "w") as f:
            await f.write(json.dumps({
                "id": entry.id,
                "content": entry.content,
                "memory_type": entry.memory_type.value,
                "file_path": entry.file_path,
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
                "version": entry.version,
                "tags": entry.tags,
                "metadata": entry.metadata,
            }, default=str))

    async def _load_from_disk(self) -> None:
        """Load project memory from disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        import os
        
        project_dir = f"{self.storage_path}/projects/{self.project_id}"
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)
            return
        
        for filename in os.listdir(project_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(project_dir, filename)
                try:
                    async with aiofiles.open(filepath, "r") as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        entry = ProjectMemoryEntry(
                            id=data["id"],
                            content=data["content"],
                            memory_type=ProjectMemoryType(data.get("memory_type", "document")),
                            file_path=data.get("file_path"),
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                            version=data.get("version", 1),
                            tags=data.get("tags", []),
                            metadata=data.get("metadata", {}),
                        )
                        
                        self._entries[entry.id] = entry
                        self._by_type[entry.memory_type].append(entry.id)
                        
                        if entry.file_path:
                            self._by_file[entry.file_path] = entry.id
                except Exception:
                    pass
