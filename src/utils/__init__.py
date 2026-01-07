"""
Utilities package.
"""

from .logger import get_logger, setup_logger, console
from .validators import (
    ValidationError,
    validate_image_file,
    validate_image_files,
    validate_notion_database_id,
    validate_api_key,
    validate_learning_style,
    validate_note_detail_level,
)
from .error_handlers import (
    StudyAssistantError,
    ConfigurationError,
    APIError,
    ProcessingError,
    StorageError,
    handle_error,
    error_handler_decorator,
)
from .prompt_templates import PromptTemplates

__all__ = [
    "get_logger",
    "setup_logger",
    "console",
    "ValidationError",
    "validate_image_file",
    "validate_image_files",
    "validate_notion_database_id",
    "validate_api_key",
    "validate_learning_style",
    "validate_note_detail_level",
    "StudyAssistantError",
    "ConfigurationError",
    "APIError",
    "ProcessingError",
    "StorageError",
    "handle_error",
    "error_handler_decorator",
    "PromptTemplates",
]