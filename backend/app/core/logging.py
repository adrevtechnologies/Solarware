"""Logging configuration for Solarware application."""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None
) -> logging.Logger:
    """Configure application logging with file and console handlers.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional file path for logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("solarware")
    logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = setup_logging(log_file="./logs/solarware.log")
