"""Phase 2: Update AgentDecision and TradingAgent models for multi-agent system

Revision ID: 001_phase2_update
Revises:
Create Date: 2025-01-05

This migration updates the database schema to support Phase 2 AI Integration:
1. Restructures agent_decisions table with parsed decision fields
2. Adds risk management parameters to trading_agents table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_phase2_update'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema for Phase 2."""

    # ============================================================================
    # 1. Update trading_agents table - Add risk management parameters
    # ============================================================================

    op.add_column('trading_agents',
        sa.Column('max_position_size', sa.DECIMAL(precision=5, scale=2),
                  nullable=False, server_default='20.0',
                  comment='Max position size as % of account value')
    )
    op.add_column('trading_agents',
        sa.Column('max_leverage', sa.Integer(),
                  nullable=False, server_default='10',
                  comment='Maximum allowed leverage (1-50x)')
    )
    op.add_column('trading_agents',
        sa.Column('stop_loss_pct', sa.DECIMAL(precision=5, scale=2),
                  nullable=False, server_default='2.0',
                  comment='Stop loss percentage')
    )
    op.add_column('trading_agents',
        sa.Column('take_profit_pct', sa.DECIMAL(precision=5, scale=2),
                  nullable=False, server_default='5.0',
                  comment='Take profit percentage')
    )
    op.add_column('trading_agents',
        sa.Column('strategy_description', sa.Text(), nullable=True,
                  comment='Description of trading strategy for this agent')
    )

    # ============================================================================
    # 2. Update agent_decisions table - Restructure for Phase 2
    # ============================================================================

    # Drop old constraints first
    op.drop_constraint('check_agent_decisions_execution_status', 'agent_decisions', type_='check')

    # Rename/drop old columns
    op.drop_column('agent_decisions', 'market_data_snapshot')
    op.drop_column('agent_decisions', 'llm_prompt')
    op.drop_column('agent_decisions', 'parsed_decision')
    op.drop_column('agent_decisions', 'execution_result')
    op.drop_column('agent_decisions', 'processing_time_ms')

    # Rename execution_status to status
    op.alter_column('agent_decisions', 'execution_status',
                    new_column_name='status',
                    existing_type=sa.String(20))

    # Make llm_response optional
    op.alter_column('agent_decisions', 'llm_response',
                    existing_type=sa.Text(),
                    nullable=True)

    # Add new decision fields
    op.add_column('agent_decisions',
        sa.Column('action', sa.String(20), nullable=False,
                  comment='OPEN_LONG, OPEN_SHORT, CLOSE_POSITION, or HOLD')
    )
    op.add_column('agent_decisions',
        sa.Column('coin', sa.String(10), nullable=False,
                  comment='BTC, ETH, SOL, BNB, DOGE, or XRP')
    )
    op.add_column('agent_decisions',
        sa.Column('size_usd', sa.DECIMAL(precision=20, scale=2), nullable=False,
                  comment='Position size in USD (0 for HOLD/CLOSE)')
    )
    op.add_column('agent_decisions',
        sa.Column('leverage', sa.Integer(), nullable=False,
                  comment='Leverage 1-50x (1 for HOLD/CLOSE)')
    )
    op.add_column('agent_decisions',
        sa.Column('stop_loss_price', sa.DECIMAL(precision=20, scale=2), nullable=False,
                  comment='Stop loss price (0 for HOLD/CLOSE)')
    )
    op.add_column('agent_decisions',
        sa.Column('take_profit_price', sa.DECIMAL(precision=20, scale=2), nullable=False,
                  comment='Take profit price (0 for HOLD/CLOSE)')
    )
    op.add_column('agent_decisions',
        sa.Column('confidence', sa.DECIMAL(precision=3, scale=2), nullable=False,
                  comment='Confidence score 0.00-1.00')
    )
    op.add_column('agent_decisions',
        sa.Column('reasoning', sa.Text(), nullable=False,
                  comment="LLM's reasoning for the decision")
    )
    op.add_column('agent_decisions',
        sa.Column('execution_time_ms', sa.Integer(), nullable=True,
                  comment='Time taken for LLM call in milliseconds')
    )

    # Create new check constraints
    op.create_check_constraint(
        'check_agent_decisions_status',
        'agent_decisions',
        "status IN ('success', 'failed', 'parsing_error')"
    )
    op.create_check_constraint(
        'check_agent_decisions_action',
        'agent_decisions',
        "action IN ('OPEN_LONG', 'OPEN_SHORT', 'CLOSE_POSITION', 'HOLD')"
    )
    op.create_check_constraint(
        'check_agent_decisions_coin',
        'agent_decisions',
        "coin IN ('BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP')"
    )
    op.create_check_constraint(
        'check_agent_decisions_leverage',
        'agent_decisions',
        "leverage >= 1 AND leverage <= 50"
    )
    op.create_check_constraint(
        'check_agent_decisions_confidence',
        'agent_decisions',
        "confidence >= 0.00 AND confidence <= 1.00"
    )

    # Create indexes for better query performance
    op.create_index('ix_agent_decisions_action', 'agent_decisions', ['action'])
    op.create_index('ix_agent_decisions_coin', 'agent_decisions', ['coin'])


def downgrade() -> None:
    """Downgrade database schema (rollback Phase 2 changes)."""

    # ============================================================================
    # 1. Rollback trading_agents changes
    # ============================================================================

    op.drop_column('trading_agents', 'strategy_description')
    op.drop_column('trading_agents', 'take_profit_pct')
    op.drop_column('trading_agents', 'stop_loss_pct')
    op.drop_column('trading_agents', 'max_leverage')
    op.drop_column('trading_agents', 'max_position_size')

    # ============================================================================
    # 2. Rollback agent_decisions changes
    # ============================================================================

    # Drop new indexes
    op.drop_index('ix_agent_decisions_coin', 'agent_decisions')
    op.drop_index('ix_agent_decisions_action', 'agent_decisions')

    # Drop new constraints
    op.drop_constraint('check_agent_decisions_confidence', 'agent_decisions', type_='check')
    op.drop_constraint('check_agent_decisions_leverage', 'agent_decisions', type_='check')
    op.drop_constraint('check_agent_decisions_coin', 'agent_decisions', type_='check')
    op.drop_constraint('check_agent_decisions_action', 'agent_decisions', type_='check')
    op.drop_constraint('check_agent_decisions_status', 'agent_decisions', type_='check')

    # Drop new columns
    op.drop_column('agent_decisions', 'execution_time_ms')
    op.drop_column('agent_decisions', 'reasoning')
    op.drop_column('agent_decisions', 'confidence')
    op.drop_column('agent_decisions', 'take_profit_price')
    op.drop_column('agent_decisions', 'stop_loss_price')
    op.drop_column('agent_decisions', 'leverage')
    op.drop_column('agent_decisions', 'size_usd')
    op.drop_column('agent_decisions', 'coin')
    op.drop_column('agent_decisions', 'action')

    # Restore old columns (with default/dummy data since we can't restore actual data)
    op.add_column('agent_decisions',
        sa.Column('processing_time_ms', sa.Integer(), nullable=True)
    )
    op.add_column('agent_decisions',
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('agent_decisions',
        sa.Column('parsed_decision', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column('agent_decisions',
        sa.Column('llm_prompt', sa.Text(), nullable=False, server_default='')
    )
    op.add_column('agent_decisions',
        sa.Column('market_data_snapshot', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default='{}')
    )

    # Rename status back to execution_status
    op.alter_column('agent_decisions', 'status',
                    new_column_name='execution_status',
                    existing_type=sa.String(20))

    # Make llm_response required again
    op.alter_column('agent_decisions', 'llm_response',
                    existing_type=sa.Text(),
                    nullable=False,
                    server_default='')

    # Restore old constraint
    op.create_check_constraint(
        'check_agent_decisions_execution_status',
        'agent_decisions',
        "execution_status IN ('pending', 'executed', 'failed', 'skipped')"
    )
