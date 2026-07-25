"""Initial migration - create core tables

Revision ID: 001
Revises: 
Create Date: 2026-07-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=200), nullable=False),
        sa.Column('goal', sa.Text(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False, server_default='custom'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='idle'),
        sa.Column('max_iterations', sa.Integer(), server_default='100'),
        sa.Column('max_tokens', sa.Integer(), server_default='128000'),
        sa.Column('timeout_seconds', sa.Integer(), server_default='3600'),
        sa.Column('budget', sa.Float(), server_default='100.0'),
        sa.Column('temperature', sa.Float(), server_default='0.7'),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('skills', postgresql.JSON(), server_default='[]'),
        sa.Column('tools', postgresql.JSON(), server_default='[]'),
        sa.Column('current_metrics', postgresql.JSON(), server_default='{}'),
        sa.Column('extra_metadata', postgresql.JSON(), server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    
    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('dependencies', postgresql.JSON(), server_default='[]'),
        sa.Column('result', postgresql.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('retries', sa.Integer(), server_default='0'),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('extra_metadata', postgresql.JSON(), server_default='{}'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    
    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('steps', postgresql.JSON(), server_default='[]'),
        sa.Column('variables', postgresql.JSON(), server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='created'),
        sa.Column('execution_count', sa.Integer(), server_default='0'),
        sa.Column('last_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(), server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflows_id'), 'workflows', ['id'], unique=False)
    
    # Create memories table
    op.create_table('memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(length=50), nullable=False, server_default='short_term'),
        sa.Column('project_id', sa.String(length=100), nullable=True),
        sa.Column('agent_id', sa.String(length=100), nullable=True),
        sa.Column('importance', sa.Float(), server_default='1.0'),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), server_default='[]'),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(), server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
    op.drop_index(op.f('ix_workflows_id'), table_name='workflows')
    op.drop_table('workflows')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.drop_table('agents')
