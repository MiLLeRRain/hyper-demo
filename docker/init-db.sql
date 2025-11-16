-- PostgreSQL 16 Initialization Script for Trading Bot
-- This script is automatically executed when the container is first created

\echo '=========================================='
\echo 'Trading Bot Database Initialization'
\echo 'PostgreSQL 16'
\echo '=========================================='

-- Ensure we're connected to the correct database
\c trading_bot_dev

-- Enable UUID extension (PostgreSQL 16 has gen_random_uuid() built-in)
-- But we'll enable the extension for compatibility
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\echo 'Creating database tables...'

-- 1. Trading Agents Table
CREATE TABLE IF NOT EXISTS trading_agents (
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

CREATE INDEX IF NOT EXISTS idx_trading_agents_llm_model ON trading_agents(llm_model);
CREATE INDEX IF NOT EXISTS idx_trading_agents_status ON trading_agents(status);

\echo 'Created table: trading_agents'

-- 2. Agent Decisions Table
CREATE TABLE IF NOT EXISTS agent_decisions (
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

CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_id ON agent_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_timestamp ON agent_decisions(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_status ON agent_decisions(status);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_action ON agent_decisions(action);
CREATE INDEX IF NOT EXISTS idx_agent_decisions_coin ON agent_decisions(coin);

\echo 'Created table: agent_decisions'

-- 3. Agent Trades Table
CREATE TABLE IF NOT EXISTS agent_trades (
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

CREATE INDEX IF NOT EXISTS idx_agent_trades_agent_id ON agent_trades(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_trades_coin ON agent_trades(coin);
CREATE INDEX IF NOT EXISTS idx_agent_trades_entry_time ON agent_trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_agent_trades_status ON agent_trades(status);

\echo 'Created table: agent_trades'

-- 4. Agent Performance Table
CREATE TABLE IF NOT EXISTS agent_performance (
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

CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_id ON agent_performance(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_snapshot_time ON agent_performance(snapshot_time);

\echo 'Created table: agent_performance'

-- 5. Bot State Table
CREATE TABLE IF NOT EXISTS bot_state (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

\echo 'Created table: bot_state'

-- Insert sample data (optional - for development)
\echo 'Inserting sample data...'

-- Sample agents
INSERT INTO trading_agents (name, llm_model, exchange_account, initial_balance, strategy_description)
VALUES
    ('Conservative Trader', 'deepseek-chat', 'testnet_account', 10000.00, 'Low-risk trend following strategy'),
    ('Aggressive Scalper', 'deepseek-chat', 'testnet_account', 5000.00, 'High-frequency scalping with tight stops')
ON CONFLICT (name) DO NOTHING;

-- Initial bot state
INSERT INTO bot_state (key, value)
VALUES ('trading_bot_state', '{"initialized": true, "version": "1.0"}')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

\echo '=========================================='
\echo 'Database initialization completed!'
\echo '=========================================='
\echo ''
\echo 'Tables created:'
\echo '  - trading_agents'
\echo '  - agent_decisions'
\echo '  - agent_trades'
\echo '  - agent_performance'
\echo '  - bot_state'
\echo ''
\echo 'Sample data:'
\echo '  - 2 sample agents'
\echo '  - Initial bot state'
\echo ''
\echo 'Database is ready to use!'
\echo '=========================================='
