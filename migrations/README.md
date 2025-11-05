# Database Migrations

This directory contains Alembic database migrations for the HyperLiquid Trading Bot.

## Setup

Install Alembic if not already installed:

```bash
pip install alembic==2.9.0
```

## Running Migrations

### Apply migrations (upgrade to latest):

```bash
# From project root
alembic upgrade head
```

### Rollback migrations (downgrade):

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### View migration history:

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Creating New Migrations

### Auto-generate migration from model changes:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create empty migration:

```bash
alembic revision -m "Description of changes"
```

## Migration Files

- **001_phase2_agent_decision_update.py**: Phase 2 schema updates
  - Updates `agent_decisions` table with parsed decision fields
  - Adds risk management parameters to `trading_agents` table

## Database Configuration

Migrations use the database URL from your environment or config file. Set the connection string in `alembic.ini` or via environment variable:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/hyperliquid_trading"
```

## Important Notes

1. **Always backup your database before running migrations in production**
2. **Test migrations on a development database first**
3. **Review auto-generated migrations before applying them**
4. **Never edit migrations that have already been applied to production**

## Phase 2 Migration Details

The Phase 2 migration (`001_phase2_agent_decision_update.py`) makes the following changes:

### Trading Agents Table
- Adds `max_position_size` (DECIMAL): Max position size as % of account
- Adds `max_leverage` (INTEGER): Maximum allowed leverage (1-50x)
- Adds `stop_loss_pct` (DECIMAL): Stop loss percentage
- Adds `take_profit_pct` (DECIMAL): Take profit percentage
- Adds `strategy_description` (TEXT): Trading strategy description

### Agent Decisions Table
- Restructures table to store parsed decision fields directly
- Replaces `execution_status` with `status` (success/failed/parsing_error)
- Adds decision fields: `action`, `coin`, `size_usd`, `leverage`
- Adds price fields: `stop_loss_price`, `take_profit_price`
- Adds `confidence` (DECIMAL 0.00-1.00): AI confidence score
- Adds `reasoning` (TEXT): LLM's decision reasoning
- Adds `execution_time_ms` (INTEGER): LLM call duration
- Makes `llm_response` optional
- Removes `market_data_snapshot`, `llm_prompt`, `parsed_decision`, `execution_result`

This restructuring enables:
- Faster queries (indexed columns vs JSON parsing)
- Type safety at database level
- Better analytics and reporting
- Direct SQL queries on decision data
