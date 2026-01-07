"""
Local SQLite database manager for caching and metadata.
"""

import json
import aiosqlite
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manager for local SQLite database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file (uses settings if not provided)
        """
        settings = get_settings()
        self.db_path = db_path or settings.database_path
        self._initialized = False
        
        logger.info(f"Database manager initialized: {self.db_path}")
    
    async def initialize(self):
        """Create database tables if they don't exist."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Processed notes table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS processed_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    notion_page_id TEXT,
                    subject TEXT,
                    title TEXT,
                    topics TEXT,
                    word_count INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Study plans table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS study_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    notion_page_id TEXT,
                    priority_subjects TEXT,
                    total_hours REAL,
                    completion REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # User preferences cache
            await db.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # API usage stats
            await db.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    tokens INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Processing queue
            await db.execute("""
                CREATE TABLE IF NOT EXISTS processing_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            
            await db.commit()
        
        self._initialized = True
        logger.info("Database tables initialized")
    
    async def save_processed_note(
        self,
        file_path: str,
        file_hash: str,
        notion_page_id: str,
        subject: str,
        title: str,
        topics: List[str],
        word_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save processed note record.
        
        Args:
            file_path: Path to source file
            file_hash: File hash for deduplication
            notion_page_id: Notion page ID
            subject: Subject name
            title: Note title
            topics: List of topics
            word_count: Word count
            metadata: Additional metadata
            
        Returns:
            Record ID
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO processed_notes 
                (file_path, file_hash, notion_page_id, subject, title, topics, word_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                file_hash,
                notion_page_id,
                subject,
                title,
                json.dumps(topics),
                word_count,
                json.dumps(metadata or {}),
            ))
            
            await db.commit()
            record_id = cursor.lastrowid
            
        logger.info(f"Saved processed note record: {file_path}")
        return record_id
    
    async def get_processed_note(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get processed note record.
        
        Args:
            file_path: Path to source file
            
        Returns:
            Note record or None
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM processed_notes WHERE file_path = ?",
                (file_path,)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
        
        return None
    
    async def check_file_processed(self, file_hash: str) -> bool:
        """
        Check if file has been processed.
        
        Args:
            file_hash: File hash
            
        Returns:
            True if processed
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM processed_notes WHERE file_hash = ?",
                (file_hash,)
            )
            count = await cursor.fetchone()
            
        return count[0] > 0
    
    async def save_study_plan(
        self,
        date: datetime,
        notion_page_id: str,
        priority_subjects: List[str],
        total_hours: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save study plan record.
        
        Args:
            date: Plan date
            notion_page_id: Notion page ID
            priority_subjects: Priority subjects
            total_hours: Total hours
            metadata: Additional metadata
            
        Returns:
            Record ID
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO study_plans 
                (date, notion_page_id, priority_subjects, total_hours, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                date.date().isoformat(),
                notion_page_id,
                json.dumps(priority_subjects),
                total_hours,
                json.dumps(metadata or {}),
            ))
            
            await db.commit()
            record_id = cursor.lastrowid
        
        logger.info(f"Saved study plan record: {date.date()}")
        return record_id
    
    async def get_study_plan(self, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get study plan for a date.
        
        Args:
            date: Plan date
            
        Returns:
            Plan record or None
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM study_plans WHERE date = ?",
                (date.date().isoformat(),)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
        
        return None
    
    async def save_preference(self, key: str, value: Any):
        """
        Save user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value)))
            
            await db.commit()
        
        logger.debug(f"Saved preference: {key}")
    
    async def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()
            
            if row:
                return json.loads(row[0])
        
        return default
    
    async def log_api_usage(
        self,
        provider: str,
        model: str,
        task: str,
        tokens: int,
    ):
        """
        Log API usage.
        
        Args:
            provider: API provider
            model: Model name
            task: Task type
            tokens: Tokens used
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO api_usage (provider, model, task, tokens)
                VALUES (?, ?, ?, ?)
            """, (provider, model, task, tokens))
            
            await db.commit()
    
    async def get_api_usage_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Usage statistics
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Total usage
            cursor = await db.execute("""
                SELECT provider, model, SUM(tokens) as total_tokens, COUNT(*) as requests
                FROM api_usage
                WHERE timestamp >= datetime('now', ? || ' days')
                GROUP BY provider, model
            """, (f"-{days}",))
            
            results = await cursor.fetchall()
            
            stats = {
                "period_days": days,
                "providers": {}
            }
            
            for row in results:
                provider, model, tokens, requests = row
                if provider not in stats["providers"]:
                    stats["providers"][provider] = {}
                
                stats["providers"][provider][model] = {
                    "total_tokens": tokens,
                    "total_requests": requests,
                }
        
        return stats
    
    async def add_to_queue(self, file_path: str) -> int:
        """
        Add file to processing queue.
        
        Args:
            file_path: Path to file
            
        Returns:
            Queue ID
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO processing_queue (file_path)
                VALUES (?)
            """, (file_path,))
            
            await db.commit()
            return cursor.lastrowid
    
    async def update_queue_status(
        self,
        queue_id: int,
        status: str,
        error: Optional[str] = None,
    ):
        """
        Update queue item status.
        
        Args:
            queue_id: Queue item ID
            status: New status
            error: Optional error message
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE processing_queue
                SET status = ?, error = ?, processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, error, queue_id))
            
            await db.commit()