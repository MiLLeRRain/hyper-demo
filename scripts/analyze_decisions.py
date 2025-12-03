#!/usr/bin/env python3
"""Analyze Agent Decisions and Trades.

This script extracts decision data from the database, correlates it with trade outcomes,
and generates a dataset for analysis or fine-tuning.

Usage:
    python scripts/analyze_decisions.py [--output data/analysis.jsonl]
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from trading_bot.models.database import AgentDecision, AgentTrade, TradingAgent
from trading_bot.infrastructure.database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    
    # Connect to Database
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    db_manager = DatabaseManager(db_url=db_url)
    session = db_manager.get_session()
    
    logger.info("Connected to database")

    # Query decisions with trades
    # We want decisions that resulted in trades, so we can see the outcome
    stmt = (
        select(AgentDecision)
        .options(joinedload(AgentDecision.trades))
        .order_by(AgentDecision.timestamp.desc())
    )
    
    results = session.execute(stmt).unique().scalars().all()
    
    logger.info(f"Found {len(results)} total decisions")
    
    analysis_data = []
    
    for decision in results:
        # Skip decisions that didn't result in a trade (HOLD or rejected)
        # unless we want to analyze missed opportunities (which is harder)
        # For now, let's focus on executed trades to judge quality.
        
        # Note: A decision might have 0 trades if it was HOLD, or if it failed execution.
        # It might have 1 trade if it was OPEN.
        # It might have multiple trades if it was a partial fill (rare here).
        
        trades = decision.trades
        
        if not trades and decision.action == "HOLD":
            # We can still analyze HOLD decisions if we had future price data to see if it was right.
            # But for now, let's skip.
            continue
            
        trade_outcome = "N/A"
        pnl = 0.0
        roi = 0.0
        
        if trades:
            trade = trades[0] # Assuming 1 trade per decision for now
            if trade.status == "closed":
                pnl = float(trade.realized_pnl or 0)
                initial_value = float(trade.size * trade.entry_price) if trade.entry_price else 1.0
                roi = (pnl / initial_value) * 100 if initial_value else 0
                trade_outcome = "WIN" if pnl > 0 else "LOSS"
            elif trade.status == "open":
                trade_outcome = "OPEN"
                # We could fetch current price to estimate PnL, but let's stick to realized for now
        
        # Construct data point
        data_point = {
            "decision_id": str(decision.id),
            "timestamp": decision.timestamp.isoformat(),
            "agent": decision.agent.name,
            "coin": decision.coin,
            "action": decision.action,
            "confidence": float(decision.confidence),
            "reasoning": decision.reasoning,
            "chain_of_thought": decision.chain_of_thought,
            "outcome": trade_outcome,
            "realized_pnl": pnl,
            "roi_percent": roi,
            "prompt_content": decision.prompt_content, # This might be large
            "llm_response": decision.llm_response
        }
        
        analysis_data.append(data_point)

    # Save to file
    output_file = Path("data/decision_analysis.jsonl")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        for item in analysis_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    logger.info(f"Exported {len(analysis_data)} analyzed decisions to {output_file}")
    
    # Print summary
    wins = len([d for d in analysis_data if d['outcome'] == 'WIN'])
    losses = len([d for d in analysis_data if d['outcome'] == 'LOSS'])
    open_trades = len([d for d in analysis_data if d['outcome'] == 'OPEN'])
    
    print("\n=== Analysis Summary ===")
    print(f"Total Decisions Analyzed: {len(analysis_data)}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    print(f"Open: {open_trades}")
    
    if wins + losses > 0:
        win_rate = (wins / (wins + losses)) * 100
        print(f"Win Rate (Closed Trades): {win_rate:.2f}%")
        
    session.close()
    db_manager.dispose()

if __name__ == "__main__":
    main()
