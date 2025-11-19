import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from trading_bot.config.models import Config
    print("Successfully imported Config")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
