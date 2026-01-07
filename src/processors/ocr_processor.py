"""
OCR and content extraction from images.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image

from src.models import ModelManager
from src.utils.logger import get_logger
from src.utils.error_handlers import ProcessingError
from src.utils.prompt_templates import PromptTemplates
from config.settings import get_settings

logger = get_logger(__name__)


class OCRProcessor:
    """Processor for OCR and content extraction from images."""
    
    def __init__(self):
        """Initialize OCR processor."""
        self.model_manager = ModelManager()
        self.settings = get_settings()
        self.prompt_templates = PromptTemplates()
        
        logger.info("OCR processor initialized")
    
    async def extract_text(
        self,
        image_path: Path,
        detail_level: Optional[str] = None,
        include_diagrams: bool = True,
    ) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            detail_level: Level of detail (minimal, standard, detailed)
            include_diagrams: Whether to describe diagrams
            
        Returns:
            Extracted text in markdown format
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            logger.info(f"Starting OCR extraction: {image_path.name}")
            
            # Get detail level from settings if not provided
            if detail_level is None:
                detail_level = self.settings.note_detail_level
            
            # Generate prompt
            prompt = self.prompt_templates.ocr_extraction_prompt(
                detail_level=detail_level,
                include_diagrams=include_diagrams,
            )
            
            # Extract text using vision model
            response = await self.model_manager.generate_with_image(
                prompt=prompt,
                image_path=image_path,
                task="ocr",
            )
            
            if not response.success:
                raise ProcessingError(
                    f"OCR extraction failed: {response.error}",
                    file_path=str(image_path),
                    stage="ocr"
                )
            
            extracted_text = response.content.strip()
            
            logger.info(
                f"OCR extraction complete: {len(extracted_text)} characters, "
                f"{response.tokens_used} tokens"
            )
            
            return extracted_text
            
        except Exception as e:
            raise ProcessingError(
                f"OCR extraction failed: {str(e)}",
                file_path=str(image_path),
                stage="ocr"
            )
    
    async def extract_from_multiple(
        self,
        image_paths: List[Path],
        detail_level: Optional[str] = None,
    ) -> List[str]:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of image file paths
            detail_level: Level of detail
            
        Returns:
            List of extracted texts
        """
        results = []
        
        for image_path in image_paths:
            try:
                text = await self.extract_text(image_path, detail_level)
                results.append(text)
            except Exception as e:
                logger.error(f"Failed to extract from {image_path.name}: {str(e)}")
                results.append(f"[ERROR: Could not extract from {image_path.name}]")
        
        return results
    
    async def extract_and_combine(
        self,
        image_paths: List[Path],
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Extract text from multiple images and combine.
        
        Args:
            image_paths: List of image file paths
            separator: Separator between extracted texts
            
        Returns:
            Combined extracted text
        """
        logger.info(f"Extracting from {len(image_paths)} images")
        
        texts = await self.extract_from_multiple(image_paths)
        combined = separator.join(texts)
        
        logger.info(f"Combined extraction: {len(combined)} characters total")
        return combined
    
    async def verify_extraction(self, extracted_text: str) -> Dict[str, Any]:
        """
        Verify quality of extracted text.
        
        Args:
            extracted_text: The extracted text
            
        Returns:
            Verification results
        """
        verification = {
            "has_content": len(extracted_text.strip()) > 0,
            "character_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "has_unclear_markers": "[UNCLEAR" in extracted_text,
            "has_diagrams": "[DIAGRAM" in extracted_text,
            "has_formulas": "$" in extracted_text,
            "has_code": "```" in extracted_text,
            "has_headings": "#" in extracted_text,
            "quality_score": 0.0,
        }
        
        # Calculate quality score
        score = 0.0
        
        if verification["has_content"]:
            score += 0.3
        
        if verification["word_count"] > 10:
            score += 0.2
        
        if verification["has_headings"]:
            score += 0.1
        
        # Penalize for unclear markers
        unclear_count = extracted_text.count("[UNCLEAR")
        if unclear_count > 0:
            penalty = min(0.3, unclear_count * 0.05)
            score -= penalty
        
        # Bonus for structured content
        if verification["has_formulas"] or verification["has_code"]:
            score += 0.1
        
        verification["quality_score"] = max(0.0, min(1.0, score + 0.3))
        
        logger.debug(f"Extraction quality score: {verification['quality_score']:.2f}")
        return verification
    
    async def extract_with_verification(
        self,
        image_path: Path,
        min_quality: float = 0.5,
        max_retries: int = 2,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Extract text with quality verification and retry.
        
        Args:
            image_path: Path to image file
            min_quality: Minimum quality score required
            max_retries: Maximum retry attempts
            
        Returns:
            Tuple of (extracted_text, verification_results)
        """
        for attempt in range(max_retries + 1):
            # Extract text
            extracted_text = await self.extract_text(image_path)
            
            # Verify quality
            verification = await self.verify_extraction(extracted_text)
            
            if verification["quality_score"] >= min_quality:
                logger.info(
                    f"Extraction verified (quality: {verification['quality_score']:.2f})"
                )
                return extracted_text, verification
            
            if attempt < max_retries:
                logger.warning(
                    f"Extraction quality low ({verification['quality_score']:.2f}), "
                    f"retrying (attempt {attempt + 2}/{max_retries + 1})"
                )
                # Try with more detail on retry
                extracted_text = await self.extract_text(
                    image_path,
                    detail_level="detailed"
                )
        
        logger.warning(f"Final quality score: {verification['quality_score']:.2f}")
        return extracted_text, verification
    
    async def extract_metadata(self, extracted_text: str) -> Dict[str, Any]:
        """
        Extract metadata from text.
        
        Args:
            extracted_text: The extracted text
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "word_count": len(extracted_text.split()),
            "character_count": len(extracted_text),
            "has_math": "$" in extracted_text or "\\(" in extracted_text,
            "has_code": "```" in extracted_text,
            "has_diagrams": "[DIAGRAM" in extracted_text,
            "has_tables": "|" in extracted_text and "---" in extracted_text,
            "heading_count": extracted_text.count("\n#"),
            "list_count": extracted_text.count("\n-") + extracted_text.count("\n*"),
        }
        
        return metadata
    
    async def post_process_ocr(self, extracted_text: str) -> str:
        """
        Post-process OCR text to fix common issues.
        
        Args:
            extracted_text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        text = extracted_text
        
        # Remove multiple blank lines
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        # Fix common OCR mistakes
        replacements = {
            " ,": ",",
            " .": ".",
            " :": ":",
            " ;": ";",
            "( ": "(",
            " )": ")",
            "[ ": "[",
            " ]": "]",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Ensure proper spacing after punctuation
        import re
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        return text.strip()
    
    def estimate_processing_time(self, image_paths: List[Path]) -> float:
        """
        Estimate processing time for images.
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimate: 5-10 seconds per image
        base_time_per_image = 7
        total_images = len(image_paths)
        
        # Add overhead for multiple images
        overhead = 2 if total_images > 1 else 0
        
        estimated_time = (base_time_per_image * total_images) + overhead
        
        logger.info(
            f"Estimated processing time: {estimated_time} seconds "
            f"for {total_images} image(s)"
        )
        
        return estimated_time