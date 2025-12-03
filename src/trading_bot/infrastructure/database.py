"""Database infrastructure module."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager handles database connections and session lifecycle.
    
    It provides:
    - Connection pooling configuration
    - Session factory
    - Context managers for transactional sessions
    - Health checks
    """

    def __init__(
        self, 
        db_url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        """
        Initialize the database manager.

        Args:
            db_url: Database connection URL
            pool_size: Number of connections to keep open inside the connection pool
            max_overflow: Number of connections to allow in overflow pool
            pool_timeout: Number of seconds to wait before giving up on getting a connection
            pool_recycle: Number of seconds after which a connection is automatically recycled
            echo: Whether to log SQL statements
        """
        self.db_url = db_url
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        
        # Configuration
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo

        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine and session factory."""
        try:
            engine_kwargs = {
                "echo": self.echo,
                "pool_recycle": self.pool_recycle
            }

            # SQLite does not support pool_size, max_overflow, pool_timeout with default pool
            if not self.db_url.startswith("sqlite"):
                engine_kwargs.update({
                    "pool_size": self.pool_size,
                    "max_overflow": self.max_overflow,
                    "pool_timeout": self.pool_timeout
                })

            self._engine = create_engine(self.db_url, **engine_kwargs)
            
            self._session_factory = sessionmaker(bind=self._engine)
            self._scoped_session = scoped_session(self._session_factory)
            
            # Log only host/db part for security, handle sqlite case
            log_url = self.db_url.split('@')[-1] if '@' in self.db_url else "sqlite_db"
            logger.info(f"Database engine initialized for {log_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    @property
    def engine(self) -> Optional[Engine]:
        """Get the SQLAlchemy engine."""
        return self._engine

    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            A new SQLAlchemy Session object.
            The caller is responsible for closing this session.
        """
        if not self._session_factory:
            raise RuntimeError("DatabaseManager not initialized")
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.session_scope() as session:
                session.add(some_object)
        
        Yields:
            Session: A SQLAlchemy session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def check_connection(self) -> bool:
        """
        Check if the database connection is working.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._scoped_session:
            self._scoped_session.remove()
        
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")
