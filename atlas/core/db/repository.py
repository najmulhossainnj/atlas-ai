"""Base repository class for database operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from atlas.core.models.base import Base


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class Repository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with CRUD operations."""
    
    def __init__(self, model: type[ModelType], session: AsyncSession):
        """Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def get(self, id: str) -> ModelType | None:
        """Get entity by ID.
        
        Args:
            id: Entity UUID
            
        Returns:
            Entity or None if not found
        """
        result = await self.session.get(self.model, id)
        return result
    
    async def get_by(self, **filters: Any) -> ModelType | None:
        """Get entity by filters.
        
        Args:
            **filters: Column = value filters
            
        Returns:
            First matching entity or None
        """
        stmt = Select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """List entities with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            **filters: Column = value filters
            
        Returns:
            List of matching entities
        """
        stmt = Select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(self, **filters: Any) -> int:
        """Count entities matching filters.
        
        Args:
            **filters: Column = value filters
            
        Returns:
            Count of matching entities
        """
        stmt = Select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def create(self, data: CreateSchemaType) -> ModelType:
        """Create new entity.
        
        Args:
            data: Pydantic model with creation data
            
        Returns:
            Created entity
        """
        # Convert Pydantic model to dict, excluding unset fields
        if hasattr(data, "model_dump"):
            model_data = data.model_dump(exclude_unset=True)
        else:
            model_data = data.dict(exclude_unset=True)
        
        # Create model instance
        instance = self.model(**model_data)
        
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        
        return instance
    
    async def update(
        self,
        id: str,
        data: UpdateSchemaType,
    ) -> ModelType | None:
        """Update entity by ID.
        
        Args:
            id: Entity UUID
            data: Pydantic model with update data
            
        Returns:
            Updated entity or None if not found
        """
        instance = await self.get(id)
        if instance is None:
            return None
        
        # Convert Pydantic model to dict, excluding unset fields
        if hasattr(data, "model_dump"):
            update_data = data.model_dump(exclude_unset=True)
        else:
            update_data = data.dict(exclude_unset=True)
        
        # Update instance attributes
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        instance.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(instance)
        
        return instance
    
    async def delete(self, id: str) -> bool:
        """Delete entity by ID (soft delete if mixin is available).
        
        Args:
            id: Entity UUID
            
        Returns:
            True if deleted, False if not found
        """
        instance = await self.get(id)
        if instance is None:
            return False
        
        # Check if soft delete is supported
        if hasattr(instance, "soft_delete") and callable(instance.soft_delete):
            instance.soft_delete()
        elif hasattr(self.model, "is_deleted"):
            # Use soft delete
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(
                    is_deleted=True,
                    deleted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await self.session.execute(stmt)
        else:
            # Hard delete
            await self.session.delete(instance)
        
        await self.session.flush()
        return True
    
    async def exists(self, **filters: Any) -> bool:
        """Check if entity exists with given filters.
        
        Args:
            **filters: Column = value filters
            
        Returns:
            True if exists, False otherwise
        """
        count = await self.count(**filters)
        return count > 0
    
    async def first(self) -> ModelType | None:
        """Get first entity ordered by ID.
        
        Returns:
            First entity or None
        """
        stmt = Select(self.model).order_by(self.model.id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def last(self) -> ModelType | None:
        """Get last entity ordered by ID.
        
        Returns:
            Last entity or None
        """
        stmt = Select(self.model).order_by(self.model.id.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
