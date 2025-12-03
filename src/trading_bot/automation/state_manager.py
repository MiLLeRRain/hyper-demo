"""State manager for trading bot state persistence."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from ..infrastructure.database import DatabaseManager

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manage trading bot state persistence.

    Stores state in database for recovery after restart.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize state manager.

        Args:
            db_manager: Database manager
        """
        self.db_manager = db_manager
        self._ensure_state_table()

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Save current state to database.

        Args:
            state: State dictionary to save
        """
        try:
            # Convert datetime objects to ISO format strings
            serialized_state = self._serialize_state(state)

            # Upsert state (PostgreSQL specific)
            query = text("""
                INSERT INTO bot_state (key, value, updated_at)
                VALUES ('trading_bot_state', :state, :updated_at)
                ON CONFLICT (key)
                DO UPDATE SET value = :state, updated_at = :updated_at
            """)

            with self.db_manager.session_scope() as session:
                session.execute(
                    query,
                    {
                        "state": str(serialized_state),
                        "updated_at": datetime.utcnow()
                    }
                )
                # Commit handled by session_scope

            logger.debug(f"State saved: {len(str(serialized_state))} bytes")

        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load last saved state from database.

        Returns:
            State dictionary or None if not found
        """
        try:
            query = text("""
                SELECT value, updated_at
                FROM bot_state
                WHERE key = 'trading_bot_state'
            """)

            with self.db_manager.session_scope() as session:
                result = session.execute(query).fetchone()

                if result:
                    state_str = result[0]
                    updated_at = result[1]

                    # Parse state string back to dict
                    state = eval(state_str)  # Safe here as we control the format

                    logger.debug(f"State loaded (last updated: {updated_at})")
                    return self._deserialize_state(state)

            logger.debug("No saved state found")
            return None

        except Exception as e:
            logger.error(f"Failed to load state: {e}", exc_info=True)
            return None

    def get_last_cycle_time(self) -> Optional[datetime]:
        """
        Get last cycle execution time.

        Returns:
            Last cycle time or None
        """
        state = self.load_state()
        if state and "last_cycle_time" in state:
            return state["last_cycle_time"]
        return None

    def get_cycle_count(self) -> int:
        """
        Get total cycle count.

        Returns:
            Cycle count
        """
        state = self.load_state()
        if state and "cycle_count" in state:
            return state["cycle_count"]
        return 0

    def increment_cycle_count(self) -> None:
        """Increment cycle count."""
        state = self.load_state() or {}
        state["cycle_count"] = state.get("cycle_count", 0) + 1
        state["last_cycle_time"] = datetime.utcnow()
        self.save_state(state)

    def record_error(self, error: str) -> None:
        """
        Record last error.

        Args:
            error: Error message
        """
        state = self.load_state() or {}
        state["last_error"] = error
        state["last_error_time"] = datetime.utcnow()
        self.save_state(state)

    def clear_state(self) -> None:
        """Clear all state (for testing)."""
        try:
            query = text("DELETE FROM bot_state WHERE key = 'trading_bot_state'")
            with self.db_manager.session_scope() as session:
                session.execute(query)
                # Commit handled by session_scope
            logger.info("State cleared")
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")

    def _ensure_state_table(self) -> None:
        """Ensure bot_state table exists."""
        try:
            # Create table if not exists
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    key VARCHAR(255) PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            with self.db_manager.session_scope() as session:
                session.execute(create_table_query)
                # Commit handled by session_scope

            logger.debug("bot_state table ensured")

        except Exception as e:
            logger.warning(f"Failed to create bot_state table: {e}")

    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize state for storage.

        Converts datetime objects to ISO format strings.

        Args:
            state: State dictionary

        Returns:
            Serialized state
        """
        serialized = {}
        for key, value in state.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized

    def _deserialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize state from storage.

        Converts ISO format strings back to datetime objects.

        Args:
            state: Serialized state

        Returns:
            Deserialized state
        """
        deserialized = {}
        for key, value in state.items():
            # Try to parse as datetime
            if isinstance(value, str) and ("time" in key.lower() or key.endswith("_at")):
                try:
                    deserialized[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    deserialized[key] = value
            else:
                deserialized[key] = value
        return deserialized

    def __repr__(self) -> str:
        """String representation."""
        cycle_count = self.get_cycle_count()
        return f"StateManager(cycle_count={cycle_count})"
