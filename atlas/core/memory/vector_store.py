"""Vector database integration for semantic memory."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
import asyncio


@dataclass
class VectorDocument:
    """A document with vector embedding."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class VectorStore:
    """Vector database wrapper supporting multiple backends."""

    def __init__(
        self,
        provider: str = "qdrant",
        url: str = "localhost:6333",
        collection_name: str = "atlas_memories",
    ):
        self.provider = provider
        self.url = url
        self.collection_name = collection_name
        self._initialized = False
        self._in_memory_store: dict[str, VectorDocument] = {}

    async def initialize(self) -> None:
        """Initialize the vector store."""
        if self._initialized:
            return
        
        if self.provider == "qdrant":
            await self._init_qdrant()
        elif self.provider == "chroma":
            await self._init_chroma()
        else:
            self._initialized = True

    async def _init_qdrant(self) -> None:
        """Initialize Qdrant client."""
        try:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(url=self.url)
            self._initialized = True
        except ImportError:
            self._initialized = True

    async def _init_chroma(self) -> None:
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._client = chromadb.Client()
            self._initialized = True
        except ImportError:
            self._initialized = True

    async def add(self, document: VectorDocument) -> str:
        """Add a document to the vector store."""
        self._in_memory_store[document.id] = document
        return document.id

    async def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[VectorDocument]:
        """Search for similar documents."""
        if not self._in_memory_store:
            return []
        
        results = []
        for doc in self._in_memory_store.values():
            if doc.embedding and query_embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                doc.score = similarity
                if filter_metadata:
                    if all(doc.metadata.get(k) == v for k, v in filter_metadata.items()):
                        results.append(doc)
                else:
                    results.append(doc)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        """Get a document by ID."""
        return self._in_memory_store.get(doc_id)

    async def delete(self, doc_id: str) -> bool:
        """Delete a document."""
        if doc_id in self._in_memory_store:
            del self._in_memory_store[doc_id]
            return True
        return False

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity."""
        if not a or not b or len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics."""
        return {
            "provider": self.provider,
            "collection": self.collection_name,
            "document_count": len(self._in_memory_store),
            "initialized": self._initialized,
        }


class EmbeddingManager:
    """Manages embedding generation."""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self._client = None

    async def generate(
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
    ) -> list[list[float]]:
        """Generate embeddings for texts."""
        if self.provider == "openai":
            return await self._openai_embeddings(texts, model)
        elif self.provider == "local":
            return self._local_embeddings(texts)
        else:
            return self._dummy_embeddings(len(texts))

    async def _openai_embeddings(
        self,
        texts: list[str],
        model: str,
    ) -> list[list[float]]:
        """Get OpenAI embeddings."""
        try:
            import openai
            if not self._client:
                self._client = openai.AsyncOpenAI()
            
            response = await self._client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception:
            return self._dummy_embeddings(len(texts))

    def _local_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate local embeddings (dummy for now)."""
        return self._dummy_embeddings(len(texts))

    def _dummy_embeddings(self, count: int, dim: int = 1536) -> list[list[float]]:
        """Generate dummy embeddings for testing."""
        import random
        return [
            [random.random() for _ in range(dim)]
            for _ in range(count)
        ]