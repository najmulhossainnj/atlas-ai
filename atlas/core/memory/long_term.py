"""Long-term memory implementation."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from atlas.core.memory.manager import MemoryEntry


class LongTermMemory:
    """Persistent storage for completed projects, strategies, and preferences."""

    def __init__(
        self,
        max_entries: int = 10000,
        ttl_days: int = 365,
        storage_path: Optional[str] = None,
    ):
        self.max_entries = max_entries
        self.ttl_days = ttl_days
        self.storage_path = storage_path
        self._store: dict[str, "MemoryEntry"] = {}
        self._categories: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the long-term memory store."""
        if self._initialized:
            return
        
        if self.storage_path:
            await self._load_from_disk()
        
        self._initialized = True

    async def add(self, entry: "MemoryEntry") -> None:
        """Add a new memory entry."""
        await self.initialize()
        
        async with self._lock:
            entry.memory_type = "long_term"
            
            if len(self._store) >= self.max_entries:
                await self._evict_oldest()
            
            self._store[entry.id] = entry
            
            category = entry.metadata.get("category", "general")
            if category not in self._categories:
                self._categories[category] = set()
            self._categories[category].add(entry.id)

            if self.storage_path:
                await self._save_to_disk(entry)

    async def get(self, entry_id: str) -> Optional["MemoryEntry"]:
        """Retrieve a memory entry by ID."""
        await self.initialize()
        
        async with self._lock:
            entry = self._store.get(entry_id)
            if entry:
                if await self._is_expired(entry):
                    await self.remove(entry_id)
                    return None
                entry.access_count += 1
                entry.accessed_at = datetime.utcnow()
            return entry

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list["MemoryEntry"]:
        """Search for entries matching the query."""
        await self.initialize()
        
        async with self._lock:
            results = []
            
            entry_ids = self._categories.get(category, set()) if category else set(self._store.keys())
            
            query_lower = query.lower()
            for entry_id in entry_ids:
                entry = self._store.get(entry_id)
                if entry and not await self._is_expired(entry):
                    if query_lower in entry.content.lower():
                        results.append(entry)
            
            results.sort(
                key=lambda x: (x.importance, x.access_count, x.created_at),
                reverse=True
            )
            return results[:limit]

    async def get_by_category(
        self,
        category: str,
        limit: int = 100,
    ) -> list["MemoryEntry"]:
        """Get all entries in a category."""
        await self.initialize()
        
        async with self._lock:
            entry_ids = self._categories.get(category, set())
            results = []
            
            for entry_id in entry_ids:
                entry = self._store.get(entry_id)
                if entry and not await self._is_expired(entry):
                    results.append(entry)
            
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[:limit]

    async def remove(self, entry_id: str) -> bool:
        """Remove a memory entry."""
        async with self._lock:
            if entry_id in self._store:
                entry = self._store.pop(entry_id)
                
                for category_entries in self._categories.values():
                    category_entries.discard(entry_id)
                
                return True
            return False

    async def clear(self) -> None:
        """Clear all long-term memories."""
        async with self._lock:
            self._store.clear()
            self._categories.clear()

    async def _is_expired(self, entry: "MemoryEntry") -> bool:
        """Check if a memory entry has expired."""
        if self.ttl_days <= 0:
            return False
        
        expiry_date = entry.created_at + timedelta(days=self.ttl_days)
        return datetime.utcnow() > expiry_date

    async def _evict_oldest(self) -> None:
        """Evict the oldest entry based on creation date."""
        if not self._store:
            return
        
        oldest_id = min(
            self._store.keys(),
            key=lambda x: self._store[x].created_at
        )
        await self.remove(oldest_id)

    async def _save_to_disk(self, entry: "MemoryEntry") -> None:
        """Save a single entry to disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        
        entry_file = f"{self.storage_path}/{entry.id}.json"
        async with aiofiles.open(entry_file, "w") as f:
            await f.write(json.dumps(entry.__dict__, default=str))

    async def _load_from_disk(self) -> None:
        """Load entries from disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        import os
        
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    async with aiofiles.open(filepath, "r") as f:
                        content = await f.read()
                        entry_data = json.loads(content)
                        
                        from atlas.core.memory.manager import MemoryEntry
                        entry = MemoryEntry(**entry_data)
                        
                        if not await self._is_expired(entry):
                            self._store[entry.id] = entry
                            
                            category = entry.metadata.get("category", "general")
                            if category not in self._categories:
                                self._categories[category] = set()
                            self._categories[category].add(entry.id)
                except Exception:
                    pass

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the memory store."""
        return {
            "type": "long_term",
            "total_entries": len(self._store),
            "max_entries": self.max_entries,
            "utilization": len(self._store) / self.max_entries if self.max_entries > 0 else 0,
            "categories": {
                cat: len(ids) for cat, ids in self._categories.items()
            },
            "ttl_days": self.ttl_days,
        }

    async def export(self) -> list[dict[str, Any]]:
        """Export all entries as dictionaries."""
        async with self._lock:
            return [
                {
                    **entry.__dict__.copy(),
                    "embedding": None,
                }
                for entry in self._store.values()
                if not await self._is_expired(entry)
            ]
