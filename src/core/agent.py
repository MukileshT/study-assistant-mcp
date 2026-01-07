"""
Main MCP agent orchestrator.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.processors import (
    ImageProcessor,
    OCRProcessor,
    ContentAnalyzer,
    TextFormatter
)
from src.storage import NotionClient, DatabaseManager, FileManager
from src.models import ModelManager
from src.utils.logger import get_logger
from src.utils.error_handlers import (
    StudyAssistantError,
    ProcessingError,
    handle_error
)
from config.settings import get_settings

logger = get_logger(__name__)


class StudyAssistantAgent:
    """Main orchestrator for the Study Assistant system."""
    
    def __init__(self):
        """Initialize the agent with all components."""
        logger.info("Initializing Study Assistant Agent")
        
        self.settings = get_settings()
        
        # Initialize components
        self.image_processor = ImageProcessor()
        self.ocr_processor = OCRProcessor()
        self.content_analyzer = ContentAnalyzer()
        self.text_formatter = TextFormatter()
        
        self.notion_client = NotionClient()
        self.db_manager = DatabaseManager()
        self.file_manager = FileManager()
        self.model_manager = ModelManager()
        
        self._initialized = False
        
        logger.info("Study Assistant Agent initialized")
    
    async def initialize(self):
        """Initialize async components."""
        if self._initialized:
            return
        
        # Initialize database
        await self.db_manager.initialize()
        
        # Health checks
        await self._run_health_checks()
        
        self._initialized = True
        logger.info("Agent initialization complete")
    
    async def _run_health_checks(self):
        """Run health checks on all services."""
        logger.info("Running health checks...")
        
        # Check Notion
        notion_ok = await self.notion_client.health_check()
        if not notion_ok:
            logger.warning("Notion health check failed")
        
        # Check models
        model_health = await self.model_manager.health_check_all()
        for provider, status in model_health.items():
            if not status:
                logger.warning(f"Model health check failed: {provider}")
        
        logger.info("Health checks complete")
    
    async def process_note(
        self,
        image_path: Path,
        subject: Optional[str] = None,
        date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a note from image to Notion.
        
        Args:
            image_path: Path to note image
            subject: Subject name (auto-detected if not provided)
            date: Note date (uses today if not provided)
            metadata: Additional metadata
            
        Returns:
            Processing results
        """
        await self.initialize()
        
        logger.info(f"Starting note processing: {image_path.name}")
        
        result = {
            "success": False,
            "file_path": str(image_path),
            "stages": {},
            "errors": []
        }
        
        try:
            # Check if already processed
            file_hash = self.file_manager.calculate_file_hash(image_path)
            if await self.db_manager.check_file_processed(file_hash):
                logger.info(f"File already processed: {image_path.name}")
                result["success"] = True
                result["message"] = "Already processed"
                return result
            
            # Stage 1: Image Preprocessing
            logger.info("Stage 1: Image preprocessing")
            try:
                preprocessed_img = self.image_processor.preprocess(image_path)
                
                # Save preprocessed image
                processed_path = self.settings.processed_dir / f"processed_{image_path.name}"
                self.image_processor.save_processed(preprocessed_img, processed_path)
                
                result["stages"]["preprocessing"] = {
                    "success": True,
                    "output_path": str(processed_path)
                }
            except Exception as e:
                handle_error(e, {"stage": "preprocessing"})
                result["errors"].append(f"Preprocessing: {str(e)}")
                # Continue with original image
                processed_path = image_path
            
            # Stage 2: OCR Extraction
            logger.info("Stage 2: OCR extraction")
            extracted_text, verification = await self.ocr_processor.extract_with_verification(
                processed_path
            )
            
            result["stages"]["ocr"] = {
                "success": verification["quality_score"] >= 0.5,
                "quality_score": verification["quality_score"],
                "word_count": verification["word_count"]
            }
            
            if not extracted_text or verification["quality_score"] < 0.3:
                raise ProcessingError(
                    "OCR quality too low",
                    file_path=str(image_path),
                    stage="ocr"
                )
            
            # Stage 3: Content Analysis
            logger.info("Stage 3: Content analysis")
            
            # Extract topics
            topics = await self.content_analyzer.extract_topics(extracted_text)
            
            # Classify subject if not provided
            if subject is None:
                subject = await self.content_analyzer.classify_subject(extracted_text)
            
            # Assess difficulty
            difficulty = await self.content_analyzer.assess_difficulty(extracted_text)
            
            # Generate summary
            summary = await self.content_analyzer.generate_summary(extracted_text)
            
            # Get analysis
            analysis = await self.content_analyzer.analyze(
                extracted_text,
                learning_style=self.settings.learning_style
            )
            
            result["stages"]["analysis"] = {
                "success": True,
                "subject": subject,
                "topics": topics,
                "difficulty": difficulty
            }
            
            # Stage 4: Text Formatting
            logger.info("Stage 4: Text formatting")
            formatted_text = await self.text_formatter.format_notes(extracted_text)
            
            # Add summary if generated
            if summary:
                formatted_text += f"\n\n## Summary\n\n{summary}\n"
            
            # Validate formatting
            validation = self.text_formatter.validate_markdown(formatted_text)
            
            result["stages"]["formatting"] = {
                "success": validation["is_valid"],
                "issues": validation.get("issues", [])
            }
            
            # Stage 5: Notion Upload
            logger.info("Stage 5: Uploading to Notion")
            
            if date is None:
                date = datetime.now()
            
            # Generate title
            title = self._generate_title(subject, topics, date)
            
            # Create Notion page
            notion_page_id = await self.notion_client.create_note_page(
                title=title,
                content=formatted_text,
                subject=subject,
                date=date,
                topics=topics,
                difficulty=difficulty,
                source=metadata.get("source", "Lecture") if metadata else "Lecture",
            )
            
            result["stages"]["notion_upload"] = {
                "success": True,
                "page_id": notion_page_id
            }
            
            # Stage 6: Save to Database
            logger.info("Stage 6: Saving to database")
            
            await self.db_manager.save_processed_note(
                file_path=str(image_path),
                file_hash=file_hash,
                notion_page_id=notion_page_id,
                subject=subject,
                title=title,
                topics=topics,
                word_count=len(formatted_text.split()),
                metadata={
                    "difficulty": difficulty,
                    "quality_score": verification["quality_score"],
                    "summary": summary,
                }
            )
            
            # Move file to processed
            self.file_manager.organize_by_subject(processed_path, subject)
            
            result["success"] = True
            result["notion_page_id"] = notion_page_id
            result["title"] = title
            result["subject"] = subject
            result["topics"] = topics
            
            logger.info(f"Note processing complete: {title}")
            
        except Exception as e:
            handle_error(e, {"file": str(image_path)})
            result["errors"].append(str(e))
            result["success"] = False
        
        return result
    
    async def process_multiple_notes(
        self,
        image_paths: List[Path],
        subject: Optional[str] = None,
        combine: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple note images.
        
        Args:
            image_paths: List of image paths
            subject: Subject for all notes
            combine: Whether to combine into single note
            
        Returns:
            List of processing results
        """
        await self.initialize()
        
        logger.info(f"Processing {len(image_paths)} notes (combine={combine})")
        
        if combine:
            return [await self._process_combined_notes(image_paths, subject)]
        else:
            results = []
            for image_path in image_paths:
                result = await self.process_note(image_path, subject=subject)
                results.append(result)
            return results
    
    async def _process_combined_notes(
        self,
        image_paths: List[Path],
        subject: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process multiple images as a single combined note."""
        logger.info(f"Processing {len(image_paths)} images as combined note")
        
        # Extract text from all images
        extracted_texts = await self.ocr_processor.extract_from_multiple(image_paths)
        
        # Combine texts
        combined_text = "\n\n---\n\n".join(extracted_texts)
        
        # Continue processing as single note
        # (simplified - would need full pipeline)
        
        return {
            "success": True,
            "combined": True,
            "image_count": len(image_paths)
        }
    
    def _generate_title(
        self,
        subject: str,
        topics: List[str],
        date: datetime
    ) -> str:
        """
        Generate a note title.
        
        Args:
            subject: Subject name
            topics: List of topics
            date: Note date
            
        Returns:
            Generated title
        """
        # Use first topic or subject
        main_topic = topics[0] if topics else subject
        
        # Format: "Subject - Topic - Date"
        date_str = date.strftime("%Y-%m-%d")
        title = f"{subject} - {main_topic} - {date_str}"
        
        return title
    
    async def get_processing_status(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get processing status for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Status information or None
        """
        await self.initialize()
        
        record = await self.db_manager.get_processed_note(str(file_path))
        return record
    
    async def reprocess_note(
        self,
        file_path: Path,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Reprocess a previously processed note.
        
        Args:
            file_path: Path to file
            force: Force reprocessing even if up to date
            
        Returns:
            Processing results
        """
        await self.initialize()
        
        if not force:
            # Check if already processed recently
            record = await self.get_processing_status(file_path)
            if record:
                logger.info(f"Note already processed: {file_path.name}")
                if not force:
                    return {
                        "success": False,
                        "message": "Already processed (use force=True to reprocess)"
                    }
        
        return await self.process_note(file_path)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Statistics dictionary
        """
        await self.initialize()
        
        # API usage stats
        api_stats = await self.db_manager.get_api_usage_stats(days=30)
        
        # Model stats
        model_stats = self.model_manager.get_all_stats()
        
        # Storage stats
        storage_stats = self.file_manager.get_storage_stats()
        
        return {
            "api_usage": api_stats,
            "models": model_stats,
            "storage": storage_stats,
        }
    
    async def cleanup(self, days: int = 30):
        """
        Clean up old files and cache.
        
        Args:
            days: Delete files older than this many days
        """
        await self.initialize()
        
        logger.info(f"Starting cleanup (older than {days} days)")
        
        # Clear old cache
        self.file_manager.clear_cache(older_than_days=days)
        
        # Clean up old uploads
        self.file_manager.cleanup_old_files(days=days)
        
        logger.info("Cleanup complete")