"""Unit tests for DatabaseManager."""

import pytest
from sqlalchemy import text
from src.trading_bot.infrastructure.database import DatabaseManager

def test_database_manager_initialization():
    """Test that DatabaseManager initializes correctly with an in-memory SQLite DB."""
    db_url = "sqlite:///:memory:"
    manager = DatabaseManager(db_url=db_url)
    
    assert manager._engine is not None
    assert manager._session_factory is not None
    assert manager._scoped_session is not None
    
    manager.dispose()

def test_database_manager_session_scope():
    """Test the session_scope context manager."""
    db_url = "sqlite:///:memory:"
    manager = DatabaseManager(db_url=db_url)
    
    # Create a dummy table for testing
    with manager.session_scope() as session:
        session.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"))
        session.execute(text("INSERT INTO test (name) VALUES ('test_item')"))
    
    # Verify data was committed
    with manager.session_scope() as session:
        result = session.execute(text("SELECT name FROM test")).scalar()
        assert result == 'test_item'
        
    manager.dispose()

def test_database_manager_check_connection():
    """Test check_connection method."""
    db_url = "sqlite:///:memory:"
    manager = DatabaseManager(db_url=db_url)
    
    assert manager.check_connection() is True
    
    manager.dispose()
