"""Semantic memory with vector embeddings for similarity search."""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from atlas.core.memory.manager import MemoryEntry


class SemanticMemory:
    """Memory system using vector embeddings for semantic search."""

    def __init__(
        self,
        embedding_dim: int = 384,
        storage_path: Optional[str] = None,
        use_chroma: bool = False,
    ):
        self.embedding_dim = embedding_dim
        self.storage_path = storage_path
        self.use_chroma = use_chroma
        self._embeddings: dict[str, list[float]] = {}
        self._content_index: dict[str, str] = {}
        self._metadata_index: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        self._chroma_client = None

    async def initialize(self) -> None:
        """Initialize the semantic memory."""
        if self._initialized:
            return
        
        if self.use_chroma:
            try:
                import chromadb
                self._chroma_client = chromadb.Client()
                self._chroma_collection = self._chroma_client.create_collection("semantic_memory")
            except ImportError:
                self.use_chroma = False
        
        if self.storage_path:
            await self._load_index()
        
        self._initialized = True

    async def create_embedding(self, text: str) -> list[float]:
        """Create a vector embedding for the given text."""
        try:
            from sentence_transformers import SentenceTransformer
            
            if not hasattr(self, "_model"):
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            
            embedding = self._model.encode(text).tolist()
            return embedding
        except ImportError:
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> list[float]:
        """Create a simple hash-based embedding when transformers is not available."""
        import hashlib
        
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        embedding = []
        for i in range(min(self.embedding_dim, len(hash_bytes) * 8)):
            byte_idx = i // 8
            bit_idx = i % 8
            value = (hash_bytes[byte_idx] >> bit_idx) & 1
            embedding.append(float(value) * 2 - 1)
        
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding[:self.embedding_dim]

    async def add(self, entry: "MemoryEntry") -> None:
        """Add a memory entry with its embedding."""
        await self.initialize()
        
        async with self._lock:
            if entry.embedding is None:
                entry.embedding = await self.create_embedding(entry.content)
            
            self._embeddings[entry.id] = entry.embedding
            self._content_index[entry.id] = entry.content
            self._metadata_index[entry.id] = {
                "importance": entry.importance,
                "created_at": entry.created_at.isoformat(),
                "metadata": entry.metadata,
            }
            
            if self.use_chroma and self._chroma_collection:
                self._chroma_collection.add(
                    ids=[entry.id],
                    embeddings=[entry.embedding],
                    documents=[entry.content],
                    metadatas=[entry.metadata],
                )

    async def get(self, entry_id: str) -> Optional["MemoryEntry"]:
        """Retrieve a memory entry by ID."""
        await self.initialize()
        
        async with self._lock:
            if entry_id not in self._content_index:
                return None
            
            from atlas.core.memory.manager import MemoryEntry
            
            return MemoryEntry(
                id=entry_id,
                content=self._content_index[entry_id],
                embedding=self._embeddings.get(entry_id),
                metadata=self._metadata_index[entry_id].get("metadata", {}),
                importance=self._metadata_index[entry_id].get("importance", 1.0),
            )

    async def search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.5,
    ) -> list["MemoryEntry"]:
        """Search for entries semantically similar to the query."""
        await self.initialize()
        
        query_embedding = await self.create_embedding(query)
        results = await self._find_similar(query_embedding, limit, threshold)
        
        return results

    async def _find_similar(
        self,
        query_embedding: list[float],
        limit: int,
        threshold: float,
    ) -> list["MemoryEntry"]:
        """Find entries with similar embeddings using cosine similarity."""
        from atlas.core.memory.manager import MemoryEntry
        
        similarities = []
        
        async with self._lock:
            for entry_id, embedding in self._embeddings.items():
                if embedding is None:
                    continue
                
                similarity = self._cosine_similarity(query_embedding, embedding)
                
                if similarity >= threshold:
                    metadata = self._metadata_index.get(entry_id, {})
                    importance = metadata.get("importance", 1.0)
                    
                    similarities.append((similarity * importance, entry_id))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, entry_id in similarities[:limit]:
            entry = await self.get(entry_id)
            if entry:
                entry.importance = score
                results.append(entry)
        
        return results

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    async def remove(self, entry_id: str) -> bool:
        """Remove a memory entry."""
        await self.initialize()
        
        async with self._lock:
            if entry_id not in self._content_index:
                return False
            
            self._embeddings.pop(entry_id, None)
            self._content_index.pop(entry_id, None)
            self._metadata_index.pop(entry_id, None)
            
            if self.use_chroma and self._chroma_collection:
                try:
                    self._chroma_collection.delete(ids=[entry_id])
                except Exception:
                    pass
            
            return True

    async def clear(self) -> None:
        """Clear all semantic memories."""
        async with self._lock:
            self._embeddings.clear()
            self._content_index.clear()
            self._metadata_index.clear()
            
            if self.use_chroma and self._chroma_collection:
                self._chroma_collection.delete()

    async def _load_index(self) -> None:
        """Load the index from disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        import os
        
        index_file = f"{self.storage_path}/semantic_index.json"
        if os.path.exists(index_file):
            try:
                async with aiofiles.open(index_file, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    self._embeddings = data.get("embeddings", {})
                    self._content_index = data.get("content_index", {})
                    self._metadata_index = data.get("metadata_index", {})
            except Exception:
                pass

    async def _save_index(self) -> None:
        """Save the index to disk."""
        if not self.storage_path:
            return
        
        import aiofiles
        import os
        
        os.makedirs(self.storage_path, exist_ok=True)
        index_file = f"{self.storage_path}/semantic_index.json"
        
        async with aiofiles.open(index_file, "w") as f:
            await f.write(json.dumps({
                "embeddings": self._embeddings,
                "content_index": self._content_index,
                "metadata_index": self._metadata_index,
            }))

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the semantic memory."""
        return {
            "type": "semantic",
            "total_entries": len(self._embeddings),
            "embedding_dim": self.embedding_dim,
            "storage_backend": "chroma" if self.use_chroma else "in_memory",
        }

    async def export(self) -> list[dict[str, Any]]:
        """Export all entries as dictionaries."""
        async with self._lock:
            return [
                {
                    "id": entry_id,
                    "content": content,
                    "embedding": self._embeddings.get(entry_id),
                    "metadata": self._metadata_index.get(entry_id, {}),
                }
                for entry_id, content in self._content_index.items()
            ]
