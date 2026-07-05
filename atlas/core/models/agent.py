"""Agent persistence model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from atlas.core.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    pass


class AgentModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Agent database model."""
    
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle")
    
    max_iterations: Mapped[int] = mapped_column(Integer, default=100)
    max_tokens: Mapped[int] = mapped_column(Integer, default=128000)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600)
    budget: Mapped[float] = mapped_column(Float, default=100.0)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    skills: Mapped[dict[str, Any]] = mapped_column(JSON, default=list)
    tools: Mapped[dict[str, Any]] = mapped_column(JSON, default=list)
    
    current_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "agent_type": self.agent_type,
            "status": self.status,
            "max_iterations": self.max_iterations,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "budget": self.budget,
            "temperature": self.temperature,
            "model": self.model,
            "skills": self.skills,
            "tools": self.tools,
            "current_metrics": self.current_metrics,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
