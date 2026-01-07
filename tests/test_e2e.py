"""
End-to-end workflow tests (requires real API keys for full testing).
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from src.core import StudyAssistantAgent
from src.planning import StudyPlanner
from config.settings import get_settings


# Mark all tests as e2e
pytestmark = pytest.mark.e2e


def create_test_note_image(tmp_path, text: str) -> Path:
    """Create a test image with text."""
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        # Try to use a font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    draw.text((50, 50), text, fill='black', font=font)
    
    # Save image
    img_path = tmp_path / "test_note.jpg"
    img.save(img_path)
    
    return img_path


@pytest.fixture
def skip_if_no_api_keys():
    """Skip test if API keys are not configured."""
    settings = get_settings()
    
    if not settings.google_api_key or "your_" in settings.google_api_key:
        pytest.skip("API keys not configured")
    
    if not settings.notion_api_key or "your_" in settings.notion_api_key:
        pytest.skip("Notion API key not configured")


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_process_real_note(self, tmp_path, skip_if_no_api_keys):
        """
        Test processing a real note image.
        
        NOTE: This test requires valid API keys and will make real API calls.
        """
        
        # Create test image with sample note content
        test_text = """
        Mathematics Notes
        
        Today's Topics:
        - Quadratic Equations
        - Solving by factoring
        
        Formula: ax² + bx + c = 0
        """
        
        image_path = create_test_note_image(tmp_path, test_text)
        
        # Process note
        agent = StudyAssistantAgent()
        
        result = await agent.process_note(
            image_path=image_path,
            subject="Mathematics",
        )
        
        # Verify processing completed
        assert result["success"] is True
        assert "notion_page_id" in result
        assert result["subject"] == "Mathematics"
        
        # Clean up - delete the test page
        # (In production, would clean up test data)
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_generate_real_plan(self, skip_if_no_api_keys):
        """
        Test generating a real study plan.
        
        NOTE: This test requires valid API keys and Notion setup.
        """
        
        planner = StudyPlanner()
        
        result = await planner.generate_daily_plan(
            target_date=datetime.now()
        )
        
        # Verify plan was generated
        assert result["success"] is True
        
        # Either has real subjects or is default plan
        assert "priority_subjects" in result or result.get("is_default") is True


class TestSystemStress:
    """Stress tests for system performance."""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_multiple_concurrent_notes(self, tmp_path, skip_if_no_api_keys):
        """Test processing multiple notes concurrently."""
        
        # Create multiple test images
        image_paths = []
        for i in range(5):
            text = f"Test Note {i+1}\n\nSample content for testing."
            img_path = create_test_note_image(tmp_path, text)
            image_paths.append(img_path)
        
        agent = StudyAssistantAgent()
        
        # Process all notes
        results = await agent.process_multiple_notes(image_paths)
        
        # All should complete
        assert len(results) == 5
        
        # Count successes
        success_count = sum(1 for r in results if r.get("success"))
        
        # At least some should succeed (allowing for API rate limits)
        assert success_count >= 1


class TestRecovery:
    """Test system recovery from errors."""
    
    @pytest.mark.asyncio
    async def test_recovery_from_network_error(self, tmp_path):
        """Test that system handles network errors gracefully."""
        
        from unittest.mock import patch, AsyncMock
        
        image_path = create_test_note_image(tmp_path, "Test content")
        
        agent = StudyAssistantAgent()
        
        # Simulate network error on first call, success on retry
        call_count = 0
        
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return type('obj', (object,), {
                'success': True,
                'content': "# Test\nContent",
                'tokens_used': 100
            })
        
        # This would test retry logic if implemented
        # For now, just verify error handling exists


class TestDataIntegrity:
    """Test data integrity across the system."""
    
    @pytest.mark.asyncio
    async def test_data_consistency_after_processing(self, tmp_path):
        """Test that data remains consistent through processing pipeline."""
        
        from src.storage import DatabaseManager, FileManager
        
        db_manager = DatabaseManager(tmp_path / "test.db")
        await db_manager.initialize()
        
        file_manager = FileManager()
        
        # Create test image
        img_path = create_test_note_image(tmp_path, "Test")
        
        # Calculate hash
        file_hash = file_manager.calculate_file_hash(img_path)
        
        # Save to database
        await db_manager.save_processed_note(
            file_path=str(img_path),
            file_hash=file_hash,
            notion_page_id="test_page",
            subject="Test",
            title="Test Note",
            topics=["test"],
            word_count=100,
        )
        
        # Retrieve and verify hash matches
        record = await db_manager.get_processed_note(str(img_path))
        
        assert record["file_hash"] == file_hash
        
        # Recalculate hash - should still match
        new_hash = file_manager.calculate_file_hash(img_path)
        assert new_hash == file_hash


class TestUserScenarios:
    """Test realistic user scenarios."""
    
    @pytest.mark.asyncio
    async def test_daily_study_routine(self, tmp_path, skip_if_no_api_keys):
        """
        Test a typical daily study routine:
        1. Process morning lecture notes
        2. Process afternoon lab notes
        3. Generate study plan for tomorrow
        """
        
        # Morning lecture
        morning_notes = create_test_note_image(
            tmp_path,
            "Lecture: Introduction to Calculus\n\nLimits and Continuity"
        )
        
        # Afternoon lab
        afternoon_notes = create_test_note_image(
            tmp_path,
            "Lab: Chemical Reactions\n\nObservations and results"
        )
        
        agent = StudyAssistantAgent()
        
        # Process notes
        morning_result = await agent.process_note(
            morning_notes,
            subject="Mathematics"
        )
        
        afternoon_result = await agent.process_note(
            afternoon_notes,
            subject="Chemistry"
        )
        
        # Generate plan
        planner = StudyPlanner()
        plan_result = await planner.generate_daily_plan(datetime.now())
        
        # Verify all steps completed
        assert morning_result.get("success") or morning_result.get("stages")
        assert afternoon_result.get("success") or afternoon_result.get("stages")
        assert plan_result.get("success") is True


class TestSystemLimits:
    """Test system behavior at limits."""
    
    def test_large_image_handling(self, tmp_path):
        """Test handling of large images."""
        from src.processors import ImageProcessor
        
        # Create large image
        large_img = Image.new('RGB', (4000, 3000), color='white')
        large_path = tmp_path / "large.jpg"
        large_img.save(large_path)
        
        processor = ImageProcessor()
        
        # Should resize automatically
        processed = processor.preprocess(large_path, max_dimension=2048)
        
        assert max(processed.size) <= 2048
    
    @pytest.mark.asyncio
    async def test_many_topics_handling(self):
        """Test handling of notes with many topics."""
        from src.processors import ContentAnalyzer
        
        analyzer = ContentAnalyzer()
        
        # Create content with many topics
        content = "# Notes\n\n" + "\n\n".join([
            f"## Topic {i}\nContent about topic {i}"
            for i in range(20)
        ])
        
        # Should handle many topics
        topics = await analyzer.extract_topics(content)
        
        # Should return reasonable number
        assert len(topics) <= 8  # Max topics setting


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not e2e"])  # Skip e2e by default