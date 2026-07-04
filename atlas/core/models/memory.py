"""Memory persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column

from atlas.core.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    pass


class MemoryModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Memory database model."""
    
    __tablename__ = "memories"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, default="short_term")
    
    project_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    importance: Mapped[float] = mapped_column(Float, default=1.0)
    
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    
    embedding: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float), nullable=True)
    
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "content": self.content,
            "memory_type": self.memory_type,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
