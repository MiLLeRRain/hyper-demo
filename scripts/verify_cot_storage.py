#!/usr/bin/env python3
"""Verify Chain of Thought (CoT) storage in database.

This script runs a single decision cycle using the real LLM and Database,
then checks if the 'chain_of_thought' column is correctly populated.
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from trading_bot.models.database import AgentDecision, TradingAgent
from trading_bot.ai.agent_manager import AgentManager
from trading_bot.orchestration.multi_agent_orchestrator import MultiAgentOrchestrator
from trading_bot.data.hyperliquid_client import HyperliquidClient
from trading_bot.config.models import LLMConfig, LLMModelConfig
from trading_bot.trading.position_manager import PositionManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    # 1. Connect to Database
    import os
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n[1] Connected to Database")

    # 2. Setup Components
    # We need a mock config or load real config
    # For simplicity, we'll create a config object manually based on .env
    llm_config = LLMConfig(
        models={
            "deepseek-chat": LLMModelConfig(
                provider="official",
                official={
                    "api_key": os.getenv("DEEPSEEK_API_KEY"),
                    "base_url": "https://api.deepseek.com/v1",
                    "model_name": "deepseek-chat"
                }
            )
        }
    )
    
    agent_manager = AgentManager(session, llm_config)
    orchestrator = MultiAgentOrchestrator(session, agent_manager)
    
    # Ensure we have at least one active agent
    agents = agent_manager.agents
    if not agents:
        print("[!] No active agents found. Please run scripts/run_sync_agents.py first.")
        return
        
    print(f"[2] Initialized Orchestrator with {len(agents)} agents")
    
    # 3. Fetch Real Market Data
    client = HyperliquidClient(base_url="https://api.hyperliquid-testnet.xyz")
    
    print("[3] Fetching Market Data...")
    # We need to construct the market_data dict expected by orchestrator
    # This usually comes from DataCollector, but we'll do a simplified fetch here
    # For this test, we'll just fetch prices to avoid complex data collection setup
    # Actually, Orchestrator expects full MarketData objects. 
    # Let's use the real DataCollector if possible, or mock the data structure.
    
    # To save time/complexity, let's mock the market data structure but with real prices
    from trading_bot.models.market_data import MarketData, Price
    
    prices = client.get_all_prices()
    market_data = {}
    
    import pandas as pd
    
    for coin in ["BTC", "ETH", "SOL"]:
        if coin in prices:
            # Create a minimal MarketData object
            market_data[coin] = MarketData(
                coin=coin,
                price=prices[coin],
                klines_3m=pd.DataFrame(),
                klines_4h=pd.DataFrame(),
                indicators_3m={},
                indicators_4h={},
                mid_prices_list=[],
                volume_current_4h=0,
                volume_average_4h=0,
                open_interest=0.0,
                funding_rate=0.0
            )
            
    print(f"    Fetched data for: {list(market_data.keys())}")

    # 4. Run Decision Cycle
    print("\n[4] Running Decision Cycle (calling LLM)...")
    
    # Mock PositionManager
    class MockPositionManager:
        def get_current_positions(self, agent_id):
            return []
        def get_account_value(self, agent_id):
            from trading_bot.models.market_data import AccountInfo
            return AccountInfo(
                account_value=10000.0,
                withdrawable=10000.0,
                margin_used=0.0,
                unrealized_pnl=0.0
            )
            
    decisions = orchestrator.generate_all_decisions(
        market_data=market_data,
        position_manager=MockPositionManager()
    )
    
    print(f"\n[5] Generated {len(decisions)} decisions")
    
    # 5. Verify CoT Storage
    print("\n[6] Verifying Database Storage...")
    
    for decision in decisions:
        print(f"\n    Decision: {decision.action} {decision.coin}")
        
        # Query DB to confirm
        db_decision = session.query(AgentDecision).filter(AgentDecision.id == decision.id).first()
        
        if db_decision:
            print(f"    [OK] Found in Database (ID: {db_decision.id})")
            
            cot = db_decision.chain_of_thought
            if cot:
                print(f"    [OK] Chain of Thought stored!")
                print(f"    Keys: {list(cot.keys())}")
                print(f"    Sample: {str(cot)[:100]}...")
            else:
                print(f"    [FAIL] Chain of Thought is EMPTY/NULL")
        else:
            print(f"    [FAIL] Decision not found in Database")

if __name__ == "__main__":
    main()
