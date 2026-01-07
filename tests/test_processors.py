"""
Tests for image and text processors.
"""

import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from unittest.mock import AsyncMock, patch

from src.processors import (
    ImageProcessor,
    OCRProcessor,
    ContentAnalyzer,
    TextFormatter
)


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img = Image.new('RGB', (800, 600), color='white')
    img_path = tmp_path / "test_image.jpg"
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_text():
    """Create sample text content."""
    return """
# Introduction to Python

Python is a high-level programming language.

## Key Features
- Easy to learn
- Powerful libraries
- Great community

## Example Code
```python
def hello():
    print("Hello, World!")
```

**Important**: Python uses indentation for code blocks.
"""


class TestImageProcessor:
    """Test image processing functionality."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = ImageProcessor()
        assert processor is not None
        assert len(processor.supported_formats) > 0
    
    def test_load_image(self, sample_image):
        """Test image loading."""
        processor = ImageProcessor()
        img = processor.load_image(sample_image)
        
        assert isinstance(img, Image.Image)
        assert img.size == (800, 600)
    
    def test_auto_rotate(self, sample_image):
        """Test auto-rotation."""
        processor = ImageProcessor()
        img = processor.load_image(sample_image)
        rotated = processor.auto_rotate(img)
        
        assert isinstance(rotated, Image.Image)
    
    def test_enhance_contrast(self, sample_image):
        """Test contrast enhancement."""
        processor = ImageProcessor()
        img = processor.load_image(sample_image)
        enhanced = processor.enhance_contrast(img, factor=1.3)
        
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == img.size
    
    def test_resize_for_processing(self, sample_image):
        """Test image resizing."""
        processor = ImageProcessor()
        img = processor.load_image(sample_image)
        resized = processor.resize_for_processing(img, max_dimension=400)
        
        assert max(resized.size) <= 400
    
    def test_preprocess(self, sample_image):
        """Test full preprocessing pipeline."""
        processor = ImageProcessor()
        result = processor.preprocess(sample_image)
        
        assert isinstance(result, Image.Image)
    
    def test_get_image_info(self, sample_image):
        """Test getting image info."""
        processor = ImageProcessor()
        info = processor.get_image_info(sample_image)
        
        assert "width" in info
        assert "height" in info
        assert info["width"] == 800
        assert info["height"] == 600


class TestOCRProcessor:
    """Test OCR processing functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test OCR processor initialization."""
        processor = OCRProcessor()
        assert processor is not None
    
    @pytest.mark.asyncio
    async def test_extract_text_mock(self, sample_image):
        """Test text extraction with mock."""
        processor = OCRProcessor()
        
        mock_response = type('obj', (object,), {
            'success': True,
            'content': "# Test Note\nSome content here.",
            'tokens_used': 100
        })
        
        with patch.object(
            processor.model_manager,
            'generate_with_image',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await processor.extract_text(sample_image)
            
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_verify_extraction(self):
        """Test extraction verification."""
        processor = OCRProcessor()
        
        text = "# Heading\n\nSome content with **bold** text."
        verification = await processor.verify_extraction(text)
        
        assert verification["has_content"] is True
        assert verification["has_headings"] is True
        assert verification["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_extract_metadata(self):
        """Test metadata extraction."""
        processor = OCRProcessor()
        
        text = "Test $x^2$ with ```code``` and tables"
        metadata = await processor.extract_metadata(text)
        
        assert "word_count" in metadata
        assert metadata["has_math"] is True
        assert metadata["has_code"] is True
    
    def test_estimate_processing_time(self, sample_image):
        """Test processing time estimation."""
        processor = OCRProcessor()
        
        time = processor.estimate_processing_time([sample_image])
        assert time > 0


class TestContentAnalyzer:
    """Test content analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test content analyzer initialization."""
        analyzer = ContentAnalyzer()
        assert analyzer is not None
    
    @pytest.mark.asyncio
    async def test_extract_topics_fallback(self, sample_text):
        """Test fallback topic extraction."""
        analyzer = ContentAnalyzer()
        topics = analyzer._extract_topics_fallback(sample_text)
        
        assert isinstance(topics, list)
        assert len(topics) > 0
    
    @pytest.mark.asyncio
    async def test_classify_subject_fallback(self, sample_text):
        """Test fallback subject classification."""
        analyzer = ContentAnalyzer()
        subjects = ["Computer Science", "Mathematics", "Other"]
        
        subject = analyzer._classify_subject_fallback(sample_text, subjects)
        
        assert subject in subjects
    
    @pytest.mark.asyncio
    async def test_assess_difficulty_fallback(self, sample_text):
        """Test fallback difficulty assessment."""
        analyzer = ContentAnalyzer()
        difficulty = analyzer._assess_difficulty_fallback(sample_text)
        
        assert difficulty in ["Easy", "Medium", "Hard"]
    
    @pytest.mark.asyncio
    async def test_extract_key_concepts(self, sample_text):
        """Test key concept extraction."""
        analyzer = ContentAnalyzer()
        concepts = await analyzer.extract_key_concepts(sample_text)
        
        assert isinstance(concepts, list)
    
    def test_get_content_stats(self, sample_text):
        """Test content statistics."""
        analyzer = ContentAnalyzer()
        stats = analyzer.get_content_stats(sample_text)
        
        assert "word_count" in stats
        assert "has_headings" in stats
        assert stats["has_code"] is True


class TestTextFormatter:
    """Test text formatting functionality."""
    
    def test_initialization(self):
        """Test text formatter initialization."""
        formatter = TextFormatter()
        assert formatter is not None
    
    def test_normalize_spacing(self, sample_text):
        """Test spacing normalization."""
        formatter = TextFormatter()
        normalized = formatter._normalize_spacing(sample_text)
        
        assert "\\n\\n\\n" not in normalized
    
    def test_clean_markdown(self):
        """Test markdown cleaning."""
        formatter = TextFormatter()
        
        messy_text = "# Heading\n\n\n-Item\n-Item"
        cleaned = formatter.clean_markdown(messy_text)
        
        assert isinstance(cleaned, str)
    
    def test_create_table_of_contents(self, sample_text):
        """Test TOC creation."""
        formatter = TextFormatter()
        toc = formatter.create_table_of_contents(sample_text)
        
        if toc:  # Only if enough headings
            assert "Table of Contents" in toc
    
    def test_validate_markdown(self, sample_text):
        """Test markdown validation."""
        formatter = TextFormatter()
        validation = formatter.validate_markdown(sample_text)
        
        assert "is_valid" in validation
        assert "issues" in validation
        assert isinstance(validation["issues"], list)
    
    def test_format_code_blocks(self):
        """Test code block formatting."""
        formatter = TextFormatter()
        
        text = "```\ndef test():\n    pass\n```"
        formatted = formatter.format_code_blocks(text)
        
        assert "```python" in formatted or "```text" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])