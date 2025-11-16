"""Quick script to run database integration tests."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Now run pytest
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([
        "tests/integration/test_database_integration.py",
        "-v",
        "--tb=short",
        "-x"
    ]))
