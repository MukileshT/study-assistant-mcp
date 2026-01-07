"""
Input validation utilities.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Union
from PIL import Image

from config.settings import get_settings


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_image_file(file_path: Union[str, Path]) -> Path:
    """
    Validate image file exists and is a supported format.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If file is invalid
    """
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        raise ValidationError(f"File not found: {file_path}")
    
    # Check if it's a file (not a directory)
    if not file_path.is_file():
        raise ValidationError(f"Not a file: {file_path}")
    
    # Check file extension
    supported_extensions = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
    if file_path.suffix.lower() not in supported_extensions:
        raise ValidationError(
            f"Unsupported image format: {file_path.suffix}. "
            f"Supported formats: {', '.join(supported_extensions)}"
        )
    
    # Check file size
    settings = get_settings()
    max_size_bytes = settings.max_image_size_mb * 1024 * 1024
    file_size = file_path.stat().st_size
    
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"File too large: {size_mb:.2f}MB. "
            f"Maximum size: {settings.max_image_size_mb}MB"
        )
    
    # Try to open the image to verify it's valid
    try:
        with Image.open(file_path) as img:
            img.verify()
    except Exception as e:
        raise ValidationError(f"Invalid or corrupted image file: {str(e)}")
    
    return file_path


def validate_image_files(file_paths: List[Union[str, Path]]) -> List[Path]:
    """
    Validate multiple image files.
    
    Args:
        file_paths: List of image file paths
        
    Returns:
        List of validated Path objects
        
    Raises:
        ValidationError: If any file is invalid
    """
    if not file_paths:
        raise ValidationError("No files provided")
    
    validated_paths = []
    errors = []
    
    for path in file_paths:
        try:
            validated_paths.append(validate_image_file(path))
        except ValidationError as e:
            errors.append(str(e))
    
    if errors:
        raise ValidationError(f"Validation errors:\n" + "\n".join(errors))
    
    return validated_paths


def validate_notion_database_id(database_id: str) -> str:
    """
    Validate Notion database ID format.
    
    Args:
        database_id: Notion database ID
        
    Returns:
        Validated database ID
        
    Raises:
        ValidationError: If ID is invalid
    """
    if not database_id:
        raise ValidationError("Database ID cannot be empty")
    
    # Remove hyphens for validation
    clean_id = database_id.replace("-", "")
    
    # Check if it's a valid hex string
    if not re.match(r"^[a-f0-9]{32}$", clean_id, re.IGNORECASE):
        raise ValidationError(
            f"Invalid Notion database ID format: {database_id}. "
            "Expected 32 character hex string (with or without hyphens)"
        )
    
    return database_id


def validate_api_key(api_key: str, service: str) -> str:
    """
    Validate API key format.
    
    Args:
        api_key: API key string
        service: Service name (for error messages)
        
    Returns:
        Validated API key
        
    Raises:
        ValidationError: If key is invalid
    """
    if not api_key:
        raise ValidationError(f"{service} API key cannot be empty")
    
    if len(api_key) < 20:
        raise ValidationError(f"{service} API key seems too short")
    
    # Check for placeholder values
    placeholder_values = [
        "your_api_key_here",
        "your_key_here",
        "placeholder",
        "xxx",
    ]
    
    if api_key.lower() in placeholder_values:
        raise ValidationError(
            f"{service} API key appears to be a placeholder. "
            "Please set your actual API key in .env file"
        )
    
    return api_key


def validate_learning_style(style: str) -> str:
    """
    Validate learning style value.
    
    Args:
        style: Learning style string
        
    Returns:
        Validated learning style
        
    Raises:
        ValidationError: If style is invalid
    """
    valid_styles = ["visual", "auditory", "kinesthetic", "reading_writing"]
    
    style = style.lower().strip()
    
    if style not in valid_styles:
        raise ValidationError(
            f"Invalid learning style: {style}. "
            f"Valid options: {', '.join(valid_styles)}"
        )
    
    return style


def validate_note_detail_level(level: str) -> str:
    """
    Validate note detail level.
    
    Args:
        level: Detail level string
        
    Returns:
        Validated detail level
        
    Raises:
        ValidationError: If level is invalid
    """
    valid_levels = ["minimal", "standard", "detailed"]
    
    level = level.lower().strip()
    
    if level not in valid_levels:
        raise ValidationError(
            f"Invalid detail level: {level}. "
            f"Valid options: {', '.join(valid_levels)}"
        )
    
    return level


def validate_date_string(date_str: str) -> str:
    """
    Validate date string format (YYYY-MM-DD).
    
    Args:
        date_str: Date string
        
    Returns:
        Validated date string
        
    Raises:
        ValidationError: If format is invalid
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValidationError(
            f"Invalid date format: {date_str}. Expected YYYY-MM-DD"
        )


def validate_time_string(time_str: str) -> str:
    """
    Validate time string format (HH:MM).
    
    Args:
        time_str: Time string
        
    Returns:
        Validated time string
        
    Raises:
        ValidationError: If format is invalid
    """
    from datetime import datetime
    
    try:
        datetime.strptime(time_str, "%H:%M")
        return time_str
    except ValueError:
        raise ValidationError(
            f"Invalid time format: {time_str}. Expected HH:MM (24-hour format)"
        )


def validate_directory(dir_path: Union[str, Path], create: bool = False) -> Path:
    """
    Validate directory exists or create it.
    
    Args:
        dir_path: Directory path
        create: Create directory if it doesn't exist
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If directory is invalid
    """
    dir_path = Path(dir_path)
    
    if not dir_path.exists():
        if create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Cannot create directory: {str(e)}")
        else:
            raise ValidationError(f"Directory not found: {dir_path}")
    
    if not dir_path.is_dir():
        raise ValidationError(f"Not a directory: {dir_path}")
    
    return dir_path