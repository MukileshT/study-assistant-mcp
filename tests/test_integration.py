"""
Integration tests for end-to-end workflows.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

from src.core import StudyAssistantAgent
from src.planning import StudyPlanner
from src.processors import ImageProcessor, OCRProcessor
from src.storage import NotionClient, DatabaseManager


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img = Image.new('RGB', (800, 600), color='white')
    img_path = tmp_path / "test_note.jpg"
    img.save(img_path)
    return img_path


@pytest.fixture
def mock_notion_response():
    """Mock Notion API responses."""
    return {
        "id": "test_page_123",
        "object": "page",
        "created_time": "2024-01-01T00:00:00.000Z",
        "properties": {}
    }


@pytest.fixture
def mock_model_response():
    """Mock model API responses."""
    return type('obj', (object,), {
        'success': True,
        'content': "# Test Note\n\nSome extracted content here.",
        'tokens_used': 100,
        'model': 'test-model',
        'provider': 'test'
    })


class TestEndToEndNoteProcessing:
    """Test complete note processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_note_processing_pipeline(self, sample_image, mock_notion_response, mock_model_response):
        """Test complete note processing from image to Notion."""
        
        agent = StudyAssistantAgent()
        
        # Mock all external API calls
        with patch.object(agent.notion_client.client.pages, 'create', new_callable=AsyncMock, return_value=mock_notion_response), \
             patch.object(agent.model_manager, 'generate_with_image', new_callable=AsyncMock, return_value=mock_model_response), \
             patch.object(agent.model_manager, 'generate', new_callable=AsyncMock, return_value=mock_model_response):
            
            # Process note
            result = await agent.process_note(
                image_path=sample_image,
                subject="Mathematics",
                date=datetime.now(),
            )
            
            # Verify result structure
            assert "success" in result
            assert "stages" in result
            
            # Check stages were executed
            assert "preprocessing" in result["stages"]
            assert "ocr" in result["stages"]
            assert "analysis" in result["stages"]
            assert "formatting" in result["stages"]
    
    @pytest.mark.asyncio
    async def test_multiple_note_processing(self, tmp_path, mock_notion_response, mock_model_response):
        """Test processing multiple notes."""
        
        # Create multiple test images
        image_paths = []
        for i in range(3):
            img = Image.new('RGB', (800, 600), color='white')
            img_path = tmp_path / f"test_note_{i}.jpg"
            img.save(img_path)
            image_paths.append(img_path)
        
        agent = StudyAssistantAgent()
        
        with patch.object(agent.notion_client.client.pages, 'create', new_callable=AsyncMock, return_value=mock_notion_response), \
             patch.object(agent.model_manager, 'generate_with_image', new_callable=AsyncMock, return_value=mock_model_response), \
             patch.object(agent.model_manager, 'generate', new_callable=AsyncMock, return_value=mock_model_response):
            
            results = await agent.process_multiple_notes(
                image_paths=image_paths,
                subject="Physics"
            )
            
            assert len(results) == 3
            # Each result should have a structure
            for result in results:
                assert "success" in result


class TestPlanningIntegration:
    """Test study planning integration."""
    
    @pytest.mark.asyncio
    async def test_plan_generation_with_notes(self, mock_notion_response, mock_model_response):
        """Test plan generation with mock notes."""
        
        planner = StudyPlanner()
        
        # Mock Notion query for recent notes
        mock_notes = {
            "results": [
                {
                    "id": "note1",
                    "properties": {
                        "Title": {"title": [{"text": {"content": "Math Notes"}}]},
                        "Subject": {"select": {"name": "Mathematics"}},
                        "Topics": {"multi_select": [{"name": "Calculus"}]},
                        "Date": {"date": {"start": "2024-01-01"}},
                        "Difficulty": {"select": {"name": "Medium"}},
                    }
                }
            ]
        }
        
        with patch.object(planner.notion_client.client.databases, 'query', new_callable=AsyncMock, return_value=mock_notes), \
             patch.object(planner.notion_client.client.pages, 'create', new_callable=AsyncMock, return_value=mock_notion_response), \
             patch.object(planner.model_manager, 'generate', new_callable=AsyncMock, return_value=mock_model_response):
            
            result = await planner.generate_daily_plan(
                target_date=datetime.now()
            )
            
            assert result["success"] is True
            assert "priority_subjects" in result
            assert "total_hours" in result
    
    @pytest.mark.asyncio
    async def test_plan_generation_without_notes(self, mock_notion_response):
        """Test default plan generation when no notes exist."""
        
        planner = StudyPlanner()
        
        # Mock empty response
        with patch.object(planner.notion_client.client.databases, 'query', new_callable=AsyncMock, return_value={"results": []}):
            
            result = await planner.generate_daily_plan(
                target_date=datetime.now()
            )
            
            # Should generate default plan
            assert result["success"] is True
            assert result.get("is_default") is True


class TestWorkflowEngine:
    """Test workflow execution."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test workflow engine execution."""
        from src.core import WorkflowEngine, WorkflowStage
        
        engine = WorkflowEngine()
        
        # Create test workflow
        workflow = engine.create_workflow("process_note")
        
        # Mock handlers
        async def mock_handler(context):
            return {"status": "success"}
        
        handlers = {
            stage.name: mock_handler
            for stage in workflow.stages
        }
        
        # Execute workflow
        completed = await engine.execute_workflow(workflow, handlers)
        
        assert completed.status == "completed"
        assert completed.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_workflow_with_failure(self):
        """Test workflow handling of failures."""
        from src.core import WorkflowEngine
        
        engine = WorkflowEngine()
        workflow = engine.create_workflow("process_note")
        
        # Handler that fails
        async def failing_handler(context):
            raise Exception("Test failure")
        
        # Handler that succeeds
        async def success_handler(context):
            return {"status": "success"}
        
        handlers = {
            workflow.stages[0].name: failing_handler,  # First stage fails
        }
        
        # Other handlers succeed
        for stage in workflow.stages[1:]:
            handlers[stage.name] = success_handler
        
        completed = await engine.execute_workflow(workflow, handlers)
        
        # Should fail if first required stage fails
        assert completed.status == "failed"


class TestDatabaseIntegration:
    """Test database operations."""
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_note(self, tmp_path):
        """Test saving and retrieving processed note."""
        
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Save note
        record_id = await db_manager.save_processed_note(
            file_path="test.jpg",
            file_hash="abc123",
            notion_page_id="page_123",
            subject="Math",
            title="Test Note",
            topics=["calculus"],
            word_count=100,
        )
        
        assert record_id > 0
        
        # Retrieve note
        record = await db_manager.get_processed_note("test.jpg")
        
        assert record is not None
        assert record["subject"] == "Math"
        assert record["title"] == "Test Note"
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_plan(self, tmp_path):
        """Test saving and retrieving study plan."""
        
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Save plan
        plan_date = datetime.now()
        record_id = await db_manager.save_study_plan(
            date=plan_date,
            notion_page_id="plan_123",
            priority_subjects=["Math", "Physics"],
            total_hours=6.0,
        )
        
        assert record_id > 0
        
        # Retrieve plan
        record = await db_manager.get_study_plan(plan_date)
        
        assert record is not None
        assert "Math" in record["priority_subjects"]


class TestErrorHandling:
    """Test error handling across components."""
    
    @pytest.mark.asyncio
    async def test_invalid_image_handling(self, tmp_path):
        """Test handling of invalid images."""
        
        # Create invalid file
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not an image")
        
        processor = ImageProcessor()
        
        with pytest.raises(Exception):
            processor.load_image(invalid_file)
    
    @pytest.mark.asyncio
    async def test_notion_api_error_handling(self):
        """Test handling of Notion API errors."""
        
        client = NotionClient()
        
        with patch.object(client.client.pages, 'create', new_callable=AsyncMock, side_effect=Exception("API Error")):
            
            with pytest.raises(Exception):
                await client.create_note_page(
                    title="Test",
                    content="Content",
                    subject="Math",
                    date=datetime.now(),
                    topics=["test"],
                )
    
    @pytest.mark.asyncio
    async def test_model_api_error_handling(self):
        """Test handling of model API errors."""
        
        from src.models import ModelManager
        
        manager = ModelManager()
        
        # Mock failing API call
        with patch.object(manager.gemini_client, 'generate', new_callable=AsyncMock, side_effect=Exception("API Error")):
            
            response = await manager.generate(
                prompt="test",
                use_fallback=False
            )
            
            assert not response.success
            assert response.error is not None


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_processing_time(self, sample_image, mock_model_response):
        """Test that processing completes in reasonable time."""
        import time
        
        agent = StudyAssistantAgent()
        
        with patch.object(agent.model_manager, 'generate_with_image', new_callable=AsyncMock, return_value=mock_model_response), \
             patch.object(agent.model_manager, 'generate', new_callable=AsyncMock, return_value=mock_model_response), \
             patch.object(agent.notion_client.client.pages, 'create', new_callable=AsyncMock, return_value={"id": "test"}):
            
            start_time = time.time()
            
            result = await agent.process_note(sample_image)
            
            elapsed = time.time() - start_time
            
            # Should complete within reasonable time (mocked, so should be fast)
            assert elapsed < 5.0  # 5 seconds max for mocked operations
    
    def test_file_manager_operations(self, tmp_path):
        """Test file manager performance."""
        from src.storage import FileManager
        
        # Create test environment
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir()
        
        manager = FileManager()
        
        # Create multiple test files
        for i in range(10):
            test_file = test_data_dir / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='white')
            img.save(test_file)
        
        # Test listing files
        import time
        start = time.time()
        
        # This should be fast even with many files
        files = list(test_data_dir.glob("*.jpg"))
        
        elapsed = time.time() - start
        
        assert len(files) == 10
        assert elapsed < 1.0  # Should be nearly instant


class TestDataConsistency:
    """Test data consistency across components."""
    
    @pytest.mark.asyncio
    async def test_notion_database_consistency(self, tmp_path):
        """Test consistency between local DB and Notion references."""
        
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Save note with Notion ID
        await db_manager.save_processed_note(
            file_path="test.jpg",
            file_hash="hash123",
            notion_page_id="notion_page_123",
            subject="Math",
            title="Test",
            topics=["topic1"],
            word_count=100,
        )
        
        # Retrieve and verify
        record = await db_manager.get_processed_note("test.jpg")
        
        assert record["notion_page_id"] == "notion_page_123"
        assert record["file_hash"] == "hash123"
    
    @pytest.mark.asyncio
    async def test_duplicate_processing_prevention(self, sample_image, tmp_path):
        """Test that duplicate files are not processed twice."""
        
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        from src.storage import FileManager
        
        file_manager = FileManager()
        file_hash = file_manager.calculate_file_hash(sample_image)
        
        # Mark as processed
        await db_manager.save_processed_note(
            file_path=str(sample_image),
            file_hash=file_hash,
            notion_page_id="page_123",
            subject="Test",
            title="Test",
            topics=[],
            word_count=0,
        )
        
        # Check if already processed
        is_processed = await db_manager.check_file_processed(file_hash)
        
        assert is_processed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])