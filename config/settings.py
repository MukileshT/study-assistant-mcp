"""
Global application settings and configuration.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    google_api_key: str = Field(..., description="Google Gemini API key")
    groq_api_key: str = Field(..., description="Groq API key")
    notion_api_key: str = Field(..., description="Notion integration token")
    notion_database_id: str = Field(..., description="Notion database ID for notes")
    notion_plans_database_id: Optional[str] = Field(
        None, description="Notion database ID for study plans"
    )
    
    # Application Settings
    app_env: str = Field("development", description="Application environment")
    log_level: str = Field("INFO", description="Logging level")
    data_dir: Path = Field(Path("./data"), description="Local data storage directory")
    max_image_size_mb: int = Field(10, description="Maximum image size in MB")
    
    # Model Configuration
    vision_model: str = Field(
        "gemini-1.5-flash", description="Primary vision model"
    )
    text_model: str = Field(
        "llama-3.1-70b-versatile", description="Primary text model"
    )
    planning_model: str = Field(
        "gemini-1.5-pro", description="Planning model"
    )
    
    # Rate Limits
    gemini_rpm_limit: int = Field(15, description="Gemini requests per minute")
    groq_rpm_limit: int = Field(30, description="Groq requests per minute")
    
    # Feature Flags
    enable_local_models: bool = Field(
        False, description="Enable local model fallback"
    )
    enable_caching: bool = Field(True, description="Enable caching")
    auto_generate_plans: bool = Field(
        True, description="Automatically generate daily plans"
    )
    plan_generation_time: str = Field(
        "20:00", description="Time to generate daily plans (HH:MM)"
    )
    
    # User Preferences
    learning_style: str = Field(
        "visual",
        description="User's learning style (visual, auditory, kinesthetic, reading_writing)"
    )
    note_detail_level: str = Field(
        "standard",
        description="Note detail level (minimal, standard, detailed)"
    )
    timezone: str = Field("America/New_York", description="User timezone")
    
    @validator("data_dir")
    def create_data_dir(cls, v):
        """Create data directory if it doesn't exist."""
        Path(v).mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (Path(v) / "cache").mkdir(exist_ok=True)
        (Path(v) / "uploads").mkdir(exist_ok=True)
        (Path(v) / "processed").mkdir(exist_ok=True)
        
        return v
    
    @validator("learning_style")
    def validate_learning_style(cls, v):
        """Validate learning style value."""
        valid_styles = ["visual", "auditory", "kinesthetic", "reading_writing"]
        if v not in valid_styles:
            raise ValueError(f"Learning style must be one of: {valid_styles}")
        return v
    
    @validator("note_detail_level")
    def validate_detail_level(cls, v):
        """Validate note detail level."""
        valid_levels = ["minimal", "standard", "detailed"]
        if v not in valid_levels:
            raise ValueError(f"Detail level must be one of: {valid_levels}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"
    
    @property
    def cache_dir(self) -> Path:
        """Get cache directory path."""
        return self.data_dir / "cache"
    
    @property
    def uploads_dir(self) -> Path:
        """Get uploads directory path."""
        return self.data_dir / "uploads"
    
    @property
    def processed_dir(self) -> Path:
        """Get processed files directory path."""
        return self.data_dir / "processed"
    
    @property
    def database_path(self) -> Path:
        """Get SQLite database path."""
        return self.data_dir / "local.db"
    
    def get_model_for_task(self, task: str) -> str:
        """
        Get the appropriate model for a specific task.
        
        Args:
            task: Task type (vision, text, planning)
            
        Returns:
            Model identifier string
        """
        task_mapping = {
            "vision": self.vision_model,
            "text": self.text_model,
            "planning": self.planning_model,
            "ocr": self.vision_model,
            "format": self.text_model,
            "analyze": self.planning_model,
        }
        return task_mapping.get(task, self.text_model)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()


# Convenience function to get specific settings
def get_api_key(service: str) -> str:
    """
    Get API key for a specific service.
    
    Args:
        service: Service name (google, groq, notion)
        
    Returns:
        API key string
        
    Raises:
        ValueError: If service is unknown
    """
    settings = get_settings()
    
    service_mapping = {
        "google": settings.google_api_key,
        "gemini": settings.google_api_key,
        "groq": settings.groq_api_key,
        "notion": settings.notion_api_key,
    }
    
    if service.lower() not in service_mapping:
        raise ValueError(f"Unknown service: {service}")
    
    return service_mapping[service.lower()]