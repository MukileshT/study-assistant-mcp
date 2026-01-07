"""
Configuration package for Study Assistant MCP.
"""

from .settings import Settings, get_settings
from .model_config import ModelConfig, get_model_config
from .notion_templates import NotionTemplates

__all__ = [
    "Settings",
    "get_settings",
    "ModelConfig",
    "get_model_config",
    "NotionTemplates",
]