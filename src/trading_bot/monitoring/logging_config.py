"""Logging configuration for trading bot.

Configures Loguru for comprehensive logging:
- Console output (colored, human-readable)
- File output (structured, rotated)
- Error file (separate error log with backtraces)
- JSON format option for log aggregation
"""

import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class LoggingConfig:
    """Logging configuration."""
    # Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    level: str = "INFO"

    # File paths
    file_path: str = "logs/trading_bot.log"
    error_file_path: str = "logs/trading_bot_error.log"

    # Rotation settings
    rotation: str = "1 day"  # Rotate daily
    retention: str = "30 days"  # Keep 30 days of logs
    compression: str = "zip"  # Compress rotated logs

    # Format options
    json_format: bool = False  # Use JSON format for file logs
    colorize_console: bool = True  # Colorize console output

    # Performance
    enqueue: bool = True  # Async logging for performance
    backtrace: bool = True  # Include backtrace on errors
    diagnose: bool = True  # Include diagnostic info


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Configure logging system.

    Sets up Loguru with multiple handlers:
    1. Console: Colored, human-readable output
    2. Main file: All logs, rotated daily
    3. Error file: Errors only, with full backtraces

    Args:
        config: Logging configuration (uses defaults if None)

    Usage:
        # Use defaults
        setup_logging()

        # Custom configuration
        config = LoggingConfig(
            level="DEBUG",
            file_path="logs/bot.log",
            json_format=True
        )
        setup_logging(config)
    """
    if config is None:
        config = LoggingConfig()

    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    log_dir = Path(config.file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    error_log_dir = Path(config.error_file_path).parent
    error_log_dir.mkdir(parents=True, exist_ok=True)

    # 1. Console handler (colored, human-readable)
    if config.colorize_console:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        console_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

    logger.add(
        sys.stdout,
        level=config.level,
        format=console_format,
        colorize=config.colorize_console,
        enqueue=config.enqueue
    )

    # 2. Main file handler (all logs)
    if config.json_format:
        # JSON format for log aggregation systems (e.g., ELK, Splunk)
        file_format = None  # Will use serialize=True
        serialize = True
    else:
        # Human-readable format
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        serialize = False

    logger.add(
        config.file_path,
        rotation=config.rotation,
        retention=config.retention,
        compression=config.compression,
        level=config.level,
        format=file_format,
        serialize=serialize,
        enqueue=config.enqueue,
        backtrace=config.backtrace,
        diagnose=config.diagnose
    )

    # 3. Error file handler (errors only, with full diagnostics)
    logger.add(
        config.error_file_path,
        rotation="1 day",
        retention="90 days",  # Keep error logs longer
        compression=config.compression,
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}\n"
            "{exception}"
        ),
        enqueue=config.enqueue,
        backtrace=True,
        diagnose=True
    )

    logger.info(f"Logging configured: level={config.level}, file={config.file_path}")


def get_logger(name: str):
    """Get a logger instance with a specific name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance

    Usage:
        from trading_bot.monitoring.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logger.bind(name=name)


# Logging best practices and usage examples
"""
# Log Level Usage Guidelines

## DEBUG
Use for detailed diagnostic information.
Typically only enabled during development or troubleshooting.

Examples:
    logger.debug(f"Market data received: {data}")
    logger.debug(f"Agent decision: {decision}")
    logger.debug(f"Database query: {query}")

## INFO
Use for general informational messages about normal operations.

Examples:
    logger.info("Trading cycle started")
    logger.info(f"Order placed: {order_id}")
    logger.info("Service started successfully")

## WARNING
Use for potentially harmful situations that don't prevent operation.

Examples:
    logger.warning("API rate limit approaching")
    logger.warning(f"Agent {agent_id} decision rejected by risk manager")
    logger.warning("High latency detected: 2.5s")

## ERROR
Use for error events that still allow the application to continue.

Examples:
    logger.error(f"Failed to execute trade: {error}")
    logger.error(f"Database connection failed, retrying...")
    logger.error(f"Agent {agent_id} threw exception: {e}")

## CRITICAL
Use for severe errors that may cause the application to abort.

Examples:
    logger.critical("Database connection lost, shutting down")
    logger.critical("Configuration file corrupted")
    logger.critical("Out of memory")

# Context Logging

Add context to log messages using bind():

    # Bind context for all subsequent logs
    context_logger = logger.bind(
        agent_id=agent_id,
        symbol=symbol,
        cycle_id=cycle_id
    )
    context_logger.info("Order placed")
    context_logger.error("Order failed")

# Exception Logging

Use logger.exception() to automatically include traceback:

    try:
        risky_operation()
    except Exception as e:
        logger.exception("Operation failed")  # Includes full traceback

Or use logger.error() with exception object:

    try:
        risky_operation()
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)

# Performance Logging

Track performance with context managers:

    with logger.contextualize(task="data_collection"):
        start = time.time()
        data = collect_data()
        duration = time.time() - start
        logger.info(f"Data collection completed in {duration:.2f}s")

# Structured Logging

For machine-readable logs, use extra fields:

    logger.bind(
        event="order_placed",
        order_id=order_id,
        symbol=symbol,
        size=size,
        price=price
    ).info("Order placed successfully")

# Security Considerations

NEVER log sensitive information:
    ❌ logger.info(f"API key: {api_key}")
    ❌ logger.info(f"Password: {password}")
    ❌ logger.info(f"Private key: {private_key}")

Instead, mask or omit:
    ✅ logger.info(f"API key: {api_key[:4]}****")
    ✅ logger.info("Authentication successful")
"""
