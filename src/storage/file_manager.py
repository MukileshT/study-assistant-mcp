"""
File management utilities for uploads and processing.
"""

import hashlib
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.validators import validate_image_file

logger = get_logger(__name__)


class FileManager:
    """Manager for file operations."""
    
    def __init__(self):
        """Initialize file manager."""
        self.settings = get_settings()
        self.uploads_dir = self.settings.uploads_dir
        self.processed_dir = self.settings.processed_dir
        self.cache_dir = self.settings.cache_dir
        
        # Ensure directories exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("File manager initialized")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def copy_to_uploads(self, source_path: Path) -> Path:
        """
        Copy file to uploads directory.
        
        Args:
            source_path: Source file path
            
        Returns:
            New file path in uploads directory
        """
        # Validate file
        validate_image_file(source_path)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{source_path.name}"
        dest_path = self.uploads_dir / filename
        
        # Copy file
        shutil.copy2(source_path, dest_path)
        logger.info(f"Copied file to uploads: {filename}")
        
        return dest_path
    
    def move_to_processed(self, file_path: Path) -> Path:
        """
        Move file to processed directory.
        
        Args:
            file_path: Current file path
            
        Returns:
            New file path in processed directory
        """
        dest_path = self.processed_dir / file_path.name
        
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"Moved file to processed: {file_path.name}")
        
        return dest_path
    
    def organize_by_subject(
        self,
        file_path: Path,
        subject: str,
        base_dir: Optional[Path] = None,
    ) -> Path:
        """
        Organize file by subject.
        
        Args:
            file_path: Current file path
            subject: Subject name
            base_dir: Base directory (uses processed_dir if not provided)
            
        Returns:
            New organized file path
        """
        base = base_dir or self.processed_dir
        subject_dir = base / subject.lower().replace(" ", "_")
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = subject_dir / file_path.name
        
        if file_path != dest_path:
            shutil.move(str(file_path), str(dest_path))
            logger.info(f"Organized file by subject: {subject}/{file_path.name}")
        
        return dest_path
    
    def organize_by_date(
        self,
        file_path: Path,
        date: datetime,
        base_dir: Optional[Path] = None,
    ) -> Path:
        """
        Organize file by date.
        
        Args:
            file_path: Current file path
            date: Date for organization
            base_dir: Base directory (uses processed_dir if not provided)
            
        Returns:
            New organized file path
        """
        base = base_dir or self.processed_dir
        date_dir = base / date.strftime("%Y") / date.strftime("%m")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = date_dir / file_path.name
        
        if file_path != dest_path:
            shutil.move(str(file_path), str(dest_path))
            logger.info(f"Organized file by date: {date.strftime('%Y/%m')}/{file_path.name}")
        
        return dest_path
    
    def get_cache_path(self, identifier: str, extension: str = ".json") -> Path:
        """
        Get cache file path for an identifier.
        
        Args:
            identifier: Unique identifier
            extension: File extension
            
        Returns:
            Cache file path
        """
        filename = f"{identifier}{extension}"
        return self.cache_dir / filename
    
    def cache_exists(self, identifier: str, extension: str = ".json") -> bool:
        """
        Check if cache file exists.
        
        Args:
            identifier: Unique identifier
            extension: File extension
            
        Returns:
            True if cache exists
        """
        cache_path = self.get_cache_path(identifier, extension)
        return cache_path.exists()
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cache directory.
        
        Args:
            older_than_days: Only clear files older than this many days
        """
        if older_than_days is None:
            # Clear all cache
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            logger.info("Cleared all cache files")
        else:
            # Clear old cache files
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            
            count = 0
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        count += 1
            
            logger.info(f"Cleared {count} old cache files (older than {older_than_days} days)")
    
    def list_uploads(self, pattern: str = "*") -> List[Path]:
        """
        List files in uploads directory.
        
        Args:
            pattern: Glob pattern
            
        Returns:
            List of file paths
        """
        return list(self.uploads_dir.glob(pattern))
    
    def list_processed(self, pattern: str = "*") -> List[Path]:
        """
        List files in processed directory.
        
        Args:
            pattern: Glob pattern
            
        Returns:
            List of file paths
        """
        files = []
        for file_path in self.processed_dir.rglob(pattern):
            if file_path.is_file():
                files.append(file_path)
        return files
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        def get_dir_size(directory: Path) -> int:
            """Calculate total size of directory."""
            total = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
            return total
        
        def count_files(directory: Path) -> int:
            """Count files in directory."""
            return sum(1 for _ in directory.rglob("*") if _.is_file())
        
        return {
            "uploads": {
                "count": count_files(self.uploads_dir),
                "size_mb": get_dir_size(self.uploads_dir) / (1024 * 1024),
            },
            "processed": {
                "count": count_files(self.processed_dir),
                "size_mb": get_dir_size(self.processed_dir) / (1024 * 1024),
            },
            "cache": {
                "count": count_files(self.cache_dir),
                "size_mb": get_dir_size(self.cache_dir) / (1024 * 1024),
            },
        }
    
    def cleanup_old_files(self, days: int = 30):
        """
        Clean up old uploaded files.
        
        Args:
            days: Delete files older than this many days
        """
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=days)
        
        count = 0
        for file_path in self.uploads_dir.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    count += 1
        
        logger.info(f"Cleaned up {count} old upload files (older than {days} days)")