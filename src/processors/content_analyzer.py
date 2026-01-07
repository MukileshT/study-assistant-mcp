"""
Content analysis and structuring.
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models import ModelManager
from src.utils.logger import get_logger
from src.utils.error_handlers import ProcessingError
from src.utils.prompt_templates import PromptTemplates
from config.settings import get_settings

logger = get_logger(__name__)


class ContentAnalyzer:
    """Analyzer for extracting structure and meaning from text content."""
    
    def __init__(self):
        """Initialize content analyzer."""
        self.model_manager = ModelManager()
        self.settings = get_settings()
        self.prompt_templates = PromptTemplates()
        
        logger.info("Content analyzer initialized")
    
    async def analyze(
        self,
        content: str,
        learning_style: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze content and extract key information.
        
        Args:
            content: Text content to analyze
            learning_style: User's learning style
            
        Returns:
            Analysis results
        """
        try:
            logger.info("Starting content analysis")
            
            if learning_style is None:
                learning_style = self.settings.learning_style
            
            # Generate analysis prompt
            prompt = self.prompt_templates.content_analysis_prompt(learning_style)
            
            full_prompt = f"{prompt}\n\nContent to analyze:\n\n{content}"
            
            # Get analysis
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="analyze",
            )
            
            if not response.success:
                raise ProcessingError(
                    f"Content analysis failed: {response.error}",
                    stage="analyze"
                )
            
            logger.info(f"Content analysis complete: {response.tokens_used} tokens")
            
            return {
                "analysis": response.content,
                "timestamp": datetime.now().isoformat(),
                "learning_style": learning_style,
            }
            
        except Exception as e:
            raise ProcessingError(
                f"Content analysis failed: {str(e)}",
                stage="analyze"
            )
    
    async def extract_topics(self, content: str) -> List[str]:
        """
        Extract main topics from content.
        
        Args:
            content: Text content
            
        Returns:
            List of topics
        """
        try:
            logger.info("Extracting topics")
            
            prompt = self.prompt_templates.topic_extraction_prompt()
            full_prompt = f"{prompt}\n\nContent:\n\n{content}"
            
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="analyze",
                temperature=0.3,
            )
            
            if not response.success:
                logger.warning(f"Topic extraction failed: {response.error}")
                return self._extract_topics_fallback(content)
            
            # Parse JSON response
            try:
                topics = json.loads(response.content)
                if isinstance(topics, list):
                    topics = [str(t).strip() for t in topics if t]
                    logger.info(f"Extracted {len(topics)} topics")
                    return topics[:8]  # Max 8 topics
            except json.JSONDecodeError:
                logger.warning("Failed to parse topics JSON, using fallback")
                return self._extract_topics_fallback(content)
            
        except Exception as e:
            logger.warning(f"Topic extraction error: {str(e)}")
            return self._extract_topics_fallback(content)
    
    def _extract_topics_fallback(self, content: str) -> List[str]:
        """
        Fallback method to extract topics using heuristics.
        
        Args:
            content: Text content
            
        Returns:
            List of topics
        """
        topics = []
        
        # Extract from headings
        heading_pattern = r'^#{1,3}\s+(.+)$'
        headings = re.findall(heading_pattern, content, re.MULTILINE)
        topics.extend(headings[:5])
        
        # If not enough topics, extract capitalized phrases
        if len(topics) < 3:
            # Find capitalized multi-word phrases
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', content)
            topics.extend(list(set(capitalized))[:3])
        
        topics = [t.strip() for t in topics if len(t.strip()) > 3]
        return topics[:5]
    
    async def classify_subject(
        self,
        content: str,
        available_subjects: Optional[List[str]] = None,
    ) -> str:
        """
        Classify content into a subject.
        
        Args:
            content: Text content
            available_subjects: List of possible subjects
            
        Returns:
            Subject name
        """
        try:
            if available_subjects is None:
                available_subjects = [
                    "Mathematics",
                    "Computer Science",
                    "Physics",
                    "Chemistry",
                    "Biology",
                    "English",
                    "History",
                    "Other"
                ]
            
            prompt = self.prompt_templates.subject_classification_prompt(
                available_subjects
            )
            full_prompt = f"{prompt}\n\nContent:\n\n{content[:1000]}"  # First 1000 chars
            
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="analyze",
                temperature=0.2,
                max_tokens=50,
            )
            
            if response.success:
                subject = response.content.strip()
                # Validate against available subjects
                if subject in available_subjects:
                    logger.info(f"Classified as subject: {subject}")
                    return subject
            
            # Fallback to keyword matching
            return self._classify_subject_fallback(content, available_subjects)
            
        except Exception as e:
            logger.warning(f"Subject classification error: {str(e)}")
            return self._classify_subject_fallback(content, available_subjects)
    
    def _classify_subject_fallback(
        self,
        content: str,
        available_subjects: List[str]
    ) -> str:
        """
        Fallback subject classification using keywords.
        
        Args:
            content: Text content
            available_subjects: List of subjects
            
        Returns:
            Subject name
        """
        content_lower = content.lower()
        
        # Subject keywords
        keywords = {
            "Mathematics": ["math", "equation", "theorem", "integral", "derivative", 
                          "algebra", "calculus", "geometry", "statistics"],
            "Computer Science": ["programming", "algorithm", "code", "function", 
                               "variable", "loop", "class", "data structure"],
            "Physics": ["force", "energy", "momentum", "velocity", "acceleration",
                       "newton", "quantum", "relativity"],
            "Chemistry": ["molecule", "atom", "reaction", "compound", "element",
                         "periodic", "bond", "acid", "base"],
            "Biology": ["cell", "organism", "gene", "protein", "evolution",
                       "species", "ecosystem", "dna"],
        }
        
        # Count keyword matches
        scores = {}
        for subject, words in keywords.items():
            if subject in available_subjects:
                score = sum(1 for word in words if word in content_lower)
                scores[subject] = score
        
        # Return subject with highest score
        if scores:
            best_subject = max(scores, key=scores.get)
            if scores[best_subject] > 0:
                return best_subject
        
        return "Other"
    
    async def assess_difficulty(self, content: str) -> str:
        """
        Assess difficulty level of content.
        
        Args:
            content: Text content
            
        Returns:
            Difficulty level (Easy, Medium, Hard)
        """
        try:
            prompt = self.prompt_templates.difficulty_assessment_prompt()
            full_prompt = f"{prompt}\n\nContent:\n\n{content[:1500]}"
            
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="analyze",
                temperature=0.2,
                max_tokens=10,
            )
            
            if response.success:
                difficulty = response.content.strip()
                if difficulty in ["Easy", "Medium", "Hard"]:
                    logger.info(f"Assessed difficulty: {difficulty}")
                    return difficulty
            
            return self._assess_difficulty_fallback(content)
            
        except Exception as e:
            logger.warning(f"Difficulty assessment error: {str(e)}")
            return self._assess_difficulty_fallback(content)
    
    def _assess_difficulty_fallback(self, content: str) -> str:
        """
        Fallback difficulty assessment using heuristics.
        
        Args:
            content: Text content
            
        Returns:
            Difficulty level
        """
        # Indicators of difficulty
        has_math = "$" in content or "∫" in content or "∑" in content
        has_code = "```" in content or "def " in content or "class " in content
        has_technical = any(
            word in content.lower()
            for word in ["theorem", "proof", "algorithm", "analysis"]
        )
        
        # Count complex words (>3 syllables roughly)
        words = content.split()
        long_words = sum(1 for word in words if len(word) > 10)
        complexity_ratio = long_words / max(len(words), 1)
        
        # Scoring
        score = 0
        if has_math:
            score += 1
        if has_code:
            score += 1
        if has_technical:
            score += 1
        if complexity_ratio > 0.1:
            score += 1
        
        if score >= 3:
            return "Hard"
        elif score >= 1:
            return "Medium"
        else:
            return "Easy"
    
    async def generate_summary(
        self,
        content: str,
        max_sentences: int = 3,
    ) -> str:
        """
        Generate a summary of content.
        
        Args:
            content: Text content
            max_sentences: Maximum number of sentences
            
        Returns:
            Summary text
        """
        try:
            prompt = self.prompt_templates.summary_generation_prompt(max_sentences)
            full_prompt = f"{prompt}\n\nContent:\n\n{content}"
            
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="analyze",
                temperature=0.5,
                max_tokens=200,
            )
            
            if response.success:
                summary = response.content.strip()
                logger.info(f"Generated summary: {len(summary)} characters")
                return summary
            
            return self._generate_summary_fallback(content, max_sentences)
            
        except Exception as e:
            logger.warning(f"Summary generation error: {str(e)}")
            return self._generate_summary_fallback(content, max_sentences)
    
    def _generate_summary_fallback(
        self,
        content: str,
        max_sentences: int
    ) -> str:
        """
        Fallback summary generation using extractive method.
        
        Args:
            content: Text content
            max_sentences: Maximum sentences
            
        Returns:
            Summary text
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return "No summary available."
        
        # Take first few sentences
        summary_sentences = sentences[:max_sentences]
        return ". ".join(summary_sentences) + "."
    
    async def extract_key_concepts(self, content: str) -> List[str]:
        """
        Extract key concepts from content.
        
        Args:
            content: Text content
            
        Returns:
            List of key concepts
        """
        # Extract from bold text
        bold_pattern = r'\*\*(.+?)\*\*'
        concepts = re.findall(bold_pattern, content)
        
        # Extract from definitions (term: definition)
        definition_pattern = r'\n-\s*(.+?):'
        definitions = re.findall(definition_pattern, content)
        
        all_concepts = list(set(concepts + definitions))
        return [c.strip() for c in all_concepts if len(c.strip()) > 2][:10]
    
    def get_content_stats(self, content: str) -> Dict[str, Any]:
        """
        Get statistics about content.
        
        Args:
            content: Text content
            
        Returns:
            Statistics dictionary
        """
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            "word_count": len(words),
            "character_count": len(content),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "has_headings": "#" in content,
            "heading_count": content.count("\n#"),
            "has_lists": ("-" in content or "*" in content),
            "has_code": "```" in content,
            "has_math": "$" in content,
            "has_images": "![" in content,
            "has_links": "[" in content and "](" in content,
        }