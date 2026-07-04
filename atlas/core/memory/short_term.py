"""Short-term memory implementation."""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from atlas.core.memory.manager import MemoryEntry


class ShortTermMemory:
    """Fast, temporary storage for active conversation and execution state."""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._store: OrderedDict[str, "MemoryEntry"] = OrderedDict()
        self._access_times: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def add(self, entry: "MemoryEntry") -> None:
        """Add a new memory entry."""
        async with self._lock:
            if len(self._store) >= self.max_entries:
                await self._evict_lru()
            
            self._store[entry.id] = entry
            self._access_times[entry.id] = datetime.utcnow()
            entry.accessed_at = datetime.utcnow()

    async def get(self, entry_id: str) -> Optional["MemoryEntry"]:
        """Retrieve a memory entry by ID."""
        async with self._lock:
            entry = self._store.get(entry_id)
            if entry:
                entry.access_count += 1
                entry.accessed_at = datetime.utcnow()
                self._access_times[entry_id] = datetime.utcnow()
                self._store.move_to_end(entry_id)
            return entry

    async def search(self, query: str, limit: int = 10) -> list["MemoryEntry"]:
        """Search for entries containing the query string."""
        async with self._lock:
            query_lower = query.lower()
            results = [
                entry for entry in self._store.values()
                if query_lower in entry.content.lower()
            ]
            results.sort(
                key=lambda x: (x.importance, x.access_count),
                reverse=True
            )
            return results[:limit]

    async def remove(self, entry_id: str) -> bool:
        """Remove a memory entry."""
        async with self._lock:
            if entry_id in self._store:
                del self._store[entry_id]
                self._access_times.pop(entry_id, None)
                return True
            return False

    async def clear(self) -> None:
        """Clear all short-term memories."""
        async with self._lock:
            self._store.clear()
            self._access_times.clear()

    async def get_recent(self, limit: int = 10) -> list["MemoryEntry"]:
        """Get the most recent memory entries."""
        async with self._lock:
            entries = list(self._store.values())
            entries.reverse()
            return entries[:limit]

    async def get_important_entries(
        self,
        threshold: float = 0.5,
    ) -> list["MemoryEntry"]:
        """Get entries with importance above threshold."""
        async with self._lock:
            return [
                entry for entry in self._store.values()
                if entry.importance >= threshold
            ]

    async def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if self._store:
            oldest_id = next(iter(self._store))
            del self._store[oldest_id]
            self._access_times.pop(oldest_id, None)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the memory store."""
        return {
            "type": "short_term",
            "total_entries": len(self._store),
            "max_entries": self.max_entries,
            "utilization": len(self._store) / self.max_entries if self.max_entries > 0 else 0,
        }

    async def export(self) -> list[dict[str, Any]]:
        """Export all entries as dictionaries."""
        async with self._lock:
            return [entry.__dict__.copy() for entry in self._store.values()]
