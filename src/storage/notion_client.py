"""
Notion API client for managing pages and databases.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from notion_client import AsyncClient
from notion_client.errors import APIResponseError

from config.settings import get_settings
from config.notion_templates import NotionTemplates
from src.utils.logger import get_logger
from src.utils.validators import validate_notion_database_id

logger = get_logger(__name__)


class NotionClient:
    """Client for interacting with Notion API."""
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion API key (uses settings if not provided)
            database_id: Default database ID (uses settings if not provided)
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.notion_api_key
        self.database_id = database_id or settings.notion_database_id
        self.plans_database_id = settings.notion_plans_database_id
        
        # Initialize async client
        self.client = AsyncClient(auth=self.api_key)
        self.templates = NotionTemplates()
        
        logger.info("Notion client initialized")
    
    async def health_check(self) -> bool:
        """
        Check if Notion API is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get the user info
            await self.client.users.me()
            logger.info("Notion API health check passed")
            return True
        except Exception as e:
            logger.error(f"Notion API health check failed: {str(e)}")
            return False
    
    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        schema: Dict[str, Any],
    ) -> str:
        """
        Create a new database.
        
        Args:
            parent_page_id: Parent page ID
            title: Database title
            schema: Database properties schema
            
        Returns:
            Created database ID
        """
        try:
            response = await self.client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties=schema,
            )
            
            database_id = response["id"]
            logger.info(f"Created database: {title} ({database_id})")
            return database_id
            
        except APIResponseError as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise
    
    async def get_database(self, database_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database information.
        
        Args:
            database_id: Database ID (uses default if not provided)
            
        Returns:
            Database object
        """
        db_id = database_id or self.database_id
        validate_notion_database_id(db_id)
        
        try:
            response = await self.client.databases.retrieve(database_id=db_id)
            logger.info(f"Retrieved database: {db_id}")
            return response
        except APIResponseError as e:
            logger.error(f"Failed to get database: {str(e)}")
            raise
    
    async def query_database(
        self,
        database_id: Optional[str] = None,
        filter_params: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query database pages.
        
        Args:
            database_id: Database ID (uses default if not provided)
            filter_params: Filter parameters
            sorts: Sort parameters
            page_size: Number of results per page
            
        Returns:
            List of page objects
        """
        db_id = database_id or self.database_id
        validate_notion_database_id(db_id)
        
        try:
            query_params = {"page_size": page_size}
            
            if filter_params:
                query_params["filter"] = filter_params
            
            if sorts:
                query_params["sorts"] = sorts
            
            response = await self.client.databases.query(
                database_id=db_id,
                **query_params
            )
            
            pages = response["results"]
            logger.info(f"Queried database: {len(pages)} pages found")
            return pages
            
        except APIResponseError as e:
            logger.error(f"Failed to query database: {str(e)}")
            raise
    
    async def create_note_page(
        self,
        title: str,
        content: str,
        subject: str,
        date: datetime,
        topics: List[str],
        database_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a note page in the database.
        
        Args:
            title: Note title
            content: Note content (markdown)
            subject: Subject name
            date: Note date
            topics: List of topics
            database_id: Database ID (uses default if not provided)
            **kwargs: Additional properties
            
        Returns:
            Created page ID
        """
        db_id = database_id or self.database_id
        validate_notion_database_id(db_id)
        
        try:
            # Create properties
            properties = self.templates.create_note_page_properties(
                title=title,
                subject=subject,
                date=date,
                topics=topics,
                status=kwargs.get("status", "Processed"),
                difficulty=kwargs.get("difficulty", "Medium"),
                source=kwargs.get("source", "Lecture"),
                word_count=len(content.split()),
            )
            
            # Convert markdown to blocks
            blocks = self.templates.markdown_to_notion_blocks(content)
            
            # Create page
            response = await self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                children=blocks,
            )
            
            page_id = response["id"]
            logger.info(f"Created note page: {title} ({page_id})")
            return page_id
            
        except APIResponseError as e:
            logger.error(f"Failed to create note page: {str(e)}")
            raise
    
    async def create_study_plan_page(
        self,
        title: str,
        content: str,
        date: datetime,
        priority_subjects: List[str],
        total_hours: float,
        database_id: Optional[str] = None,
    ) -> str:
        """
        Create a study plan page.
        
        Args:
            title: Plan title
            content: Plan content (markdown)
            date: Plan date
            priority_subjects: Priority subjects
            total_hours: Total study hours
            database_id: Database ID (uses plans DB if not provided)
            
        Returns:
            Created page ID
        """
        db_id = database_id or self.plans_database_id or self.database_id
        validate_notion_database_id(db_id)
        
        try:
            # Create properties
            properties = self.templates.create_study_plan_properties(
                title=title,
                date=date,
                priority_subjects=priority_subjects,
                total_hours=total_hours,
            )
            
            # Convert markdown to blocks
            blocks = self.templates.markdown_to_notion_blocks(content)
            
            # Create page
            response = await self.client.pages.create(
                parent={"database_id": db_id},
                properties=properties,
                children=blocks,
            )
            
            page_id = response["id"]
            logger.info(f"Created study plan page: {title} ({page_id})")
            return page_id
            
        except APIResponseError as e:
            logger.error(f"Failed to create study plan page: {str(e)}")
            raise
    
    async def update_page_properties(
        self,
        page_id: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update page properties.
        
        Args:
            page_id: Page ID
            properties: Properties to update
            
        Returns:
            Updated page object
        """
        try:
            response = await self.client.pages.update(
                page_id=page_id,
                properties=properties,
            )
            logger.info(f"Updated page properties: {page_id}")
            return response
        except APIResponseError as e:
            logger.error(f"Failed to update page: {str(e)}")
            raise
    
    async def append_blocks(
        self,
        page_id: str,
        blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Append blocks to a page.
        
        Args:
            page_id: Page ID
            blocks: Blocks to append
            
        Returns:
            API response
        """
        try:
            response = await self.client.blocks.children.append(
                block_id=page_id,
                children=blocks,
            )
            logger.info(f"Appended {len(blocks)} blocks to page: {page_id}")
            return response
        except APIResponseError as e:
            logger.error(f"Failed to append blocks: {str(e)}")
            raise
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get page information.
        
        Args:
            page_id: Page ID
            
        Returns:
            Page object
        """
        try:
            response = await self.client.pages.retrieve(page_id=page_id)
            logger.info(f"Retrieved page: {page_id}")
            return response
        except APIResponseError as e:
            logger.error(f"Failed to get page: {str(e)}")
            raise
    
    async def search_pages(
        self,
        query: str,
        filter_type: Optional[str] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search for pages.
        
        Args:
            query: Search query
            filter_type: Filter by type (page, database)
            page_size: Number of results
            
        Returns:
            List of page objects
        """
        try:
            search_params = {
                "query": query,
                "page_size": page_size,
            }
            
            if filter_type:
                search_params["filter"] = {"property": "object", "value": filter_type}
            
            response = await self.client.search(**search_params)
            results = response["results"]
            logger.info(f"Search found {len(results)} results for: {query}")
            return results
            
        except APIResponseError as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    async def get_recent_notes(
        self,
        days: int = 7,
        subject: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent notes.
        
        Args:
            days: Number of days to look back
            subject: Optional subject filter
            
        Returns:
            List of note pages
        """
        from datetime import timedelta
        
        # Calculate date filter
        start_date = datetime.now() - timedelta(days=days)
        
        # Build filter
        filter_params = {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "on_or_after": start_date.isoformat()
                    }
                }
            ]
        }
        
        # Add subject filter if provided
        if subject:
            filter_params["and"].append({
                "property": "Subject",
                "select": {
                    "equals": subject
                }
            })
        
        # Sort by date descending
        sorts = [{"property": "Date", "direction": "descending"}]
        
        return await self.query_database(
            filter_params=filter_params,
            sorts=sorts,
        )