"""
Logging configuration and utilities.
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from config.settings import get_settings


# Custom theme for rich console
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "debug": "dim",
})

# Global console instance
console = Console(theme=CUSTOM_THEME)


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(
    name: str = "study_assistant",
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logger with console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    log_level = level or settings.log_level
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with Rich
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=False,
    )
    console_handler.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(console_handler)
    
    # File handler (if specified or in production)
    if log_file or settings.is_production:
        if not log_file:
            log_dir = settings.data_dir / "logs"
            log_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"study_assistant_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "study_assistant") -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger hasn't been set up yet, set it up now
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Convenience functions for common logging patterns
def log_api_call(logger: logging.Logger, provider: str, model: str, tokens: int = 0):
    """Log an API call with details."""
    logger.info(
        f"API Call: {provider}/{model}",
        extra={"provider": provider, "model": model, "tokens": tokens}
    )


def log_processing_step(logger: logging.Logger, step: str, status: str = "started"):
    """Log a processing step."""
    logger.info(f"Processing: {step} - {status}")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: dict
):
    """Log an error with additional context."""
    logger.error(
        f"Error: {str(error)}",
        extra={"error_type": type(error).__name__, "context": context},
        exc_info=True
    )


# Create default logger instance
default_logger = get_logger()