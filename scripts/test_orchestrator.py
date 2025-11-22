
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from trading_bot.orchestration.multi_agent_orchestrator import MultiAgentOrchestrator

print("Successfully imported MultiAgentOrchestrator")
print(f"Has generate_all_decisions: {hasattr(MultiAgentOrchestrator, 'generate_all_decisions')}")
