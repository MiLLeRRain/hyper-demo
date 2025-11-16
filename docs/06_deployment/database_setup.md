# PostgreSQL Setup Guide

Complete guide to setting up PostgreSQL for the Trading Bot.

---

## Quick Start (Windows)

### 1. Install PostgreSQL

**Download**: https://www.postgresql.org/download/windows/

**Recommended version**: PostgreSQL 13+

**Installation steps**:
1. Download PostgreSQL installer
2. Run installer
3. Set password for `postgres` user (remember this!)
4. Use default port: `5432`
5. Install Stack Builder components (optional)

### 2. Verify Installation

```bash
# Check PostgreSQL is running
psql --version

# Should output: psql (PostgreSQL) 13.x or higher
```

### 3. Create Database

```bash
# Connect to PostgreSQL as postgres user
psql -U postgres

# In psql prompt:
CREATE USER trading_bot WITH PASSWORD 'trading_bot_2025';
CREATE DATABASE trading_bot_dev OWNER trading_bot;
GRANT ALL PRIVILEGES ON DATABASE trading_bot_dev TO trading_bot;
\q
```

### 4. Configure Environment

Create or update `.env`:

```bash
# Database Configuration
DB_USER=trading_bot
DB_PASSWORD=trading_bot_2025
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_bot_dev
```

### 5. Initialize Schema

```bash
# Run database initialization script
python scripts/init_database.py --sample-data
```

Expected output:
```
======================================================================
DATABASE INITIALIZATION
======================================================================
Database: localhost:5432/trading_bot_dev
Sample data: Yes
Drop existing: No
======================================================================

2025-11-16 - INFO - Testing database connection...
2025-11-16 - INFO - Successfully connected to database
2025-11-16 - INFO - Creating database tables...
2025-11-16 - INFO - Successfully created all tables
2025-11-16 - INFO - Verifying database schema...
2025-11-16 - INFO - Successfully verified all 5 tables
  trading_agents: X indexes
  agent_decisions: X indexes
  agent_trades: X indexes
  agent_performance: X indexes
  bot_state: X indexes
2025-11-16 - INFO - Creating sample data...
2025-11-16 - INFO - Created 2 sample agents
2025-11-16 - INFO - Created sample decisions
2025-11-16 - INFO - Created initial bot state

======================================================================
SUCCESS: Database initialized successfully
======================================================================

Next steps:
1. Run integration tests: pytest tests/integration/test_database_integration.py -v
2. Start the trading bot: python tradingbot.py start
```

---

## Alternative: Docker PostgreSQL

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    container_name: trading_bot_postgres
    environment:
      POSTGRES_USER: trading_bot
      POSTGRES_PASSWORD: trading_bot_2025
      POSTGRES_DB: trading_bot_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Start database**:
```bash
docker-compose up -d
```

**Stop database**:
```bash
docker-compose down
```

**View logs**:
```bash
docker-compose logs -f postgres
```

---

## Manual Database Initialization (SQL)

If you prefer to run SQL directly:

```sql
-- 1. Create database and user
CREATE USER trading_bot WITH PASSWORD 'trading_bot_2025';
CREATE DATABASE trading_bot_dev OWNER trading_bot;
GRANT ALL PRIVILEGES ON DATABASE trading_bot_dev TO trading_bot;

-- 2. Connect to the new database
\c trading_bot_dev

-- 3. Create schema (run init_database.py instead, or use these SQL statements):

-- Trading Agents table
CREATE TABLE trading_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    llm_model VARCHAR(50) NOT NULL,
    exchange_account VARCHAR(50) NOT NULL,
    initial_balance DECIMAL(20,2) NOT NULL,
    max_position_size DECIMAL(5,2) NOT NULL DEFAULT 20.0,
    max_leverage INTEGER NOT NULL DEFAULT 10,
    stop_loss_pct DECIMAL(5,2) NOT NULL DEFAULT 2.0,
    take_profit_pct DECIMAL(5,2) NOT NULL DEFAULT 5.0,
    strategy_description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT check_trading_agents_status CHECK (status IN ('active', 'paused', 'stopped'))
);

CREATE INDEX idx_trading_agents_llm_model ON trading_agents(llm_model);
CREATE INDEX idx_trading_agents_status ON trading_agents(status);

-- Agent Decisions table
CREATE TABLE agent_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES trading_agents(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    action VARCHAR(20) NOT NULL,
    coin VARCHAR(10) NOT NULL,
    size_usd DECIMAL(20,2) NOT NULL,
    leverage INTEGER NOT NULL,
    stop_loss_price DECIMAL(20,2) NOT NULL,
    take_profit_price DECIMAL(20,2) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    reasoning TEXT NOT NULL,
    llm_response TEXT,
    execution_time_ms INTEGER,
    error_message TEXT,
    CONSTRAINT check_agent_decisions_status CHECK (status IN ('success', 'failed', 'parsing_error')),
    CONSTRAINT check_agent_decisions_action CHECK (action IN ('OPEN_LONG', 'OPEN_SHORT', 'CLOSE_POSITION', 'HOLD')),
    CONSTRAINT check_agent_decisions_coin CHECK (coin IN ('BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP')),
    CONSTRAINT check_agent_decisions_leverage CHECK (leverage >= 1 AND leverage <= 50),
    CONSTRAINT check_agent_decisions_confidence CHECK (confidence >= 0.00 AND confidence <= 1.00)
);

CREATE INDEX idx_agent_decisions_agent_id ON agent_decisions(agent_id);
CREATE INDEX idx_agent_decisions_timestamp ON agent_decisions(timestamp);
CREATE INDEX idx_agent_decisions_status ON agent_decisions(status);
CREATE INDEX idx_agent_decisions_action ON agent_decisions(action);
CREATE INDEX idx_agent_decisions_coin ON agent_decisions(coin);

-- Agent Trades table
CREATE TABLE agent_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES trading_agents(id) ON DELETE CASCADE,
    decision_id UUID REFERENCES agent_decisions(id) ON DELETE SET NULL,
    coin VARCHAR(10) NOT NULL,
    side VARCHAR(10) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    entry_price DECIMAL(20,2),
    entry_time TIMESTAMP WITH TIME ZONE,
    exit_price DECIMAL(20,2),
    exit_time TIMESTAMP WITH TIME ZONE,
    realized_pnl DECIMAL(20,2),
    unrealized_pnl DECIMAL(20,2),
    fees DECIMAL(20,2),
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    hyperliquid_order_id VARCHAR(100),
    notes TEXT,
    CONSTRAINT check_agent_trades_side CHECK (side IN ('long', 'short')),
    CONSTRAINT check_agent_trades_status CHECK (status IN ('open', 'closed', 'liquidated'))
);

CREATE INDEX idx_agent_trades_agent_id ON agent_trades(agent_id);
CREATE INDEX idx_agent_trades_coin ON agent_trades(coin);
CREATE INDEX idx_agent_trades_entry_time ON agent_trades(entry_time);
CREATE INDEX idx_agent_trades_status ON agent_trades(status);

-- Agent Performance table
CREATE TABLE agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES trading_agents(id) ON DELETE CASCADE,
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_value DECIMAL(20,2) NOT NULL,
    cash_balance DECIMAL(20,2) NOT NULL,
    position_value DECIMAL(20,2) NOT NULL,
    realized_pnl DECIMAL(20,2) NOT NULL,
    unrealized_pnl DECIMAL(20,2) NOT NULL,
    total_pnl DECIMAL(20,2) NOT NULL,
    roi_percent DECIMAL(10,4),
    num_trades INTEGER DEFAULT 0,
    num_winning_trades INTEGER DEFAULT 0,
    num_losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_win DECIMAL(20,2),
    avg_loss DECIMAL(20,2),
    profit_factor DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    max_drawdown_percent DECIMAL(5,2)
);

CREATE INDEX idx_agent_performance_agent_id ON agent_performance(agent_id);
CREATE INDEX idx_agent_performance_snapshot_time ON agent_performance(snapshot_time);

-- Bot State table
CREATE TABLE bot_state (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## Verification

### Check Tables

```bash
psql -U trading_bot -d trading_bot_dev

# In psql:
\dt  # List tables

# Should show:
# trading_agents
# agent_decisions
# agent_trades
# agent_performance
# bot_state
```

### Run Integration Tests

```bash
# Test with SQLite (no PostgreSQL needed)
python run_db_tests.py

# All 22 tests should pass:
# ============================= 22 passed in 0.84s ==============================
```

### Check Sample Data

```bash
psql -U trading_bot -d trading_bot_dev

# Query sample agents
SELECT name, llm_model, initial_balance FROM trading_agents;

# Query sample decisions
SELECT action, coin, confidence FROM agent_decisions;

# Query bot state
SELECT * FROM bot_state;
```

---

## Troubleshooting

### Connection Refused

**Error**: `connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused`

**Solutions**:
1. Check PostgreSQL is running:
   ```bash
   # Windows
   services.msc  # Look for "postgresql-x64-13"

   # Or use pg_ctl
   pg_ctl status -D "C:\Program Files\PostgreSQL\13\data"
   ```

2. Start PostgreSQL:
   ```bash
   # Windows (as Administrator)
   net start postgresql-x64-13

   # Or use pg_ctl
   pg_ctl start -D "C:\Program Files\PostgreSQL\13\data"
   ```

### Authentication Failed

**Error**: `password authentication failed for user "trading_bot"`

**Solutions**:
1. Reset password:
   ```bash
   psql -U postgres
   ALTER USER trading_bot WITH PASSWORD 'trading_bot_2025';
   ```

2. Check `pg_hba.conf` allows password authentication:
   ```
   # File location: C:\Program Files\PostgreSQL\13\data\pg_hba.conf
   # Add/modify line:
   host    all             all             127.0.0.1/32            md5
   ```

3. Reload PostgreSQL:
   ```bash
   pg_ctl reload -D "C:\Program Files\PostgreSQL\13\data"
   ```

### Database Does Not Exist

**Error**: `database "trading_bot_dev" does not exist`

**Solution**:
```bash
psql -U postgres
CREATE DATABASE trading_bot_dev OWNER trading_bot;
\q
```

---

## Production Recommendations

### 1. Strong Password

```bash
# Generate strong password
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
DB_PASSWORD=<generated_strong_password>
```

### 2. Secure Configuration

**File**: `.env`
```bash
# Production database
DB_USER=trading_bot_prod
DB_PASSWORD=<strong_password_here>
DB_HOST=localhost  # Or remote DB host
DB_PORT=5432
DB_NAME=trading_bot_prod
```

**Important**: Add `.env` to `.gitignore` to prevent committing secrets!

### 3. Backups

```bash
# Backup database
pg_dump -U trading_bot trading_bot_dev > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U trading_bot trading_bot_dev < backup_20251116.sql
```

### 4. Monitoring

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('trading_bot_dev'));

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'trading_bot_dev';
```

---

## Summary

**Required steps**:
1. ✅ Install PostgreSQL 13+
2. ✅ Create `trading_bot` user
3. ✅ Create `trading_bot_dev` database
4. ✅ Configure `.env` file
5. ✅ Run `python scripts/init_database.py --sample-data`
6. ✅ Verify with `python run_db_tests.py`

**Optional**:
- Use Docker for easier management
- Set up automated backups
- Configure monitoring

You're now ready to use the database with the trading bot!
