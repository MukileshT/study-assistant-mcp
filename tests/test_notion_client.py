"""
Tests for Notion client.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.storage import NotionClient
from config.notion_templates import NotionTemplates


@pytest.fixture
def notion_client():
    """Create a test Notion client."""
    with patch.dict('os.environ', {
        'NOTION_API_KEY': 'test_key',
        'NOTION_DATABASE_ID': 'a' * 32,
    }):
        return NotionClient(
            api_key='test_key',
            database_id='a' * 32,
        )


@pytest.fixture
def mock_notion_response():
    """Create a mock Notion API response."""
    return {
        "id": "test_page_id",
        "object": "page",
        "created_time": "2024-01-01T00:00:00.000Z",
        "properties": {}
    }


class TestNotionClient:
    """Test Notion client functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, notion_client):
        """Test successful health check."""
        with patch.object(notion_client.client.users, 'me', new_callable=AsyncMock) as mock_me:
            mock_me.return_value = {"id": "test_user"}
            
            result = await notion_client.health_check()
            assert result is True
            mock_me.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, notion_client):
        """Test failed health check."""
        with patch.object(notion_client.client.users, 'me', new_callable=AsyncMock) as mock_me:
            mock_me.side_effect = Exception("API Error")
            
            result = await notion_client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_note_page(self, notion_client, mock_notion_response):
        """Test creating a note page."""
        with patch.object(
            notion_client.client.pages,
            'create',
            new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_notion_response
            
            page_id = await notion_client.create_note_page(
                title="Test Note",
                content="# Test Content\nSome text here.",
                subject="Mathematics",
                date=datetime.now(),
                topics=["Algebra", "Equations"],
            )
            
            assert page_id == "test_page_id"
            mock_create.assert_called_once()
            
            # Verify the call arguments
            call_args = mock_create.call_args
            assert call_args.kwargs["properties"]["Title"]["title"][0]["text"]["content"] == "Test Note"
    
    @pytest.mark.asyncio
    async def test_query_database(self, notion_client):
        """Test querying database."""
        mock_response = {
            "results": [
                {"id": "page1"},
                {"id": "page2"},
            ]
        }
        
        with patch.object(
            notion_client.client.databases,
            'query',
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = mock_response
            
            results = await notion_client.query_database()
            
            assert len(results) == 2
            assert results[0]["id"] == "page1"
            mock_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recent_notes(self, notion_client):
        """Test getting recent notes."""
        with patch.object(
            notion_client,
            'query_database',
            new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = [{"id": "recent_page"}]
            
            results = await notion_client.get_recent_notes(days=7)
            
            assert len(results) == 1
            mock_query.assert_called_once()


class TestNotionTemplates:
    """Test Notion template utilities."""
    
    def test_notes_database_schema(self):
        """Test notes database schema generation."""
        schema = NotionTemplates.notes_database_schema()
        
        assert "Title" in schema
        assert "Subject" in schema
        assert "Date" in schema
        assert schema["Subject"]["select"]["options"][0]["name"] == "Mathematics"
    
    def test_create_note_page_properties(self):
        """Test note page properties creation."""
        props = NotionTemplates.create_note_page_properties(
            title="Test",
            subject="Physics",
            date=datetime.now(),
            topics=["Mechanics"],
        )
        
        assert props["Title"]["title"][0]["text"]["content"] == "Test"
        assert props["Subject"]["select"]["name"] == "Physics"
        assert len(props["Topics"]["multi_select"]) == 1
    
    def test_markdown_to_notion_blocks_heading(self):
        """Test markdown heading conversion."""
        markdown = "# Main Heading\n## Subheading"
        blocks = NotionTemplates.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["type"] == "heading_1"
        assert blocks[1]["type"] == "heading_2"
    
    def test_markdown_to_notion_blocks_list(self):
        """Test markdown list conversion."""
        markdown = "- Item 1\n- Item 2"
        blocks = NotionTemplates.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["type"] == "bulleted_list_item"
    
    def test_markdown_to_notion_blocks_code(self):
        """Test markdown code block conversion."""
        markdown = "```python\nprint('hello')\n```"
        blocks = NotionTemplates.markdown_to_notion_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "code"
    
    def test_create_summary_callout(self):
        """Test callout creation."""
        callout = NotionTemplates.create_summary_callout("Test summary")
        
        assert callout["type"] == "callout"
        assert callout["callout"]["icon"]["emoji"] == "📝"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])