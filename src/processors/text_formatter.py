"""
Text formatting and markdown generation.
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

from src.models import ModelManager
from src.utils.logger import get_logger
from src.utils.error_handlers import ProcessingError
from src.utils.prompt_templates import PromptTemplates
from config.settings import get_settings

logger = get_logger(__name__)


class TextFormatter:
    """Formatter for converting and cleaning text to markdown."""
    
    def __init__(self):
        """Initialize text formatter."""
        self.model_manager = ModelManager()
        self.settings = get_settings()
        self.prompt_templates = PromptTemplates()
        
        # Load user preferences
        self.load_preferences()
        
        logger.info("Text formatter initialized")
    
    def load_preferences(self):
        """Load formatting preferences from config."""
        try:
            prefs_path = Path("config/user_preferences.json")
            if prefs_path.exists():
                with open(prefs_path, 'r') as f:
                    data = json.load(f)
                    self.style_prefs = data.get("note_formatting", {})
            else:
                self.style_prefs = {}
        except Exception as e:
            logger.warning(f"Could not load preferences: {str(e)}")
            self.style_prefs = {}
    
    async def format_notes(
        self,
        raw_text: str,
        style_preferences: Optional[Dict[str, bool]] = None,
    ) -> str:
        """
        Format raw text into clean markdown notes.
        
        Args:
            raw_text: Raw extracted text
            style_preferences: Formatting preferences
            
        Returns:
            Formatted markdown text
        """
        try:
            logger.info("Starting text formatting")
            
            # Use provided preferences or defaults
            prefs = style_preferences or self.style_prefs
            
            # Generate formatting prompt
            prompt = self.prompt_templates.formatting_prompt(prefs)
            full_prompt = f"{prompt}\n\nRaw text to format:\n\n{raw_text}"
            
            # Get formatted text
            response = await self.model_manager.generate(
                prompt=full_prompt,
                task="format",
            )
            
            if not response.success:
                raise ProcessingError(
                    f"Formatting failed: {response.error}",
                    stage="format"
                )
            
            formatted_text = response.content.strip()
            
            # Post-process
            formatted_text = self.post_process_formatting(formatted_text, prefs)
            
            logger.info(
                f"Formatting complete: {len(formatted_text)} characters, "
                f"{response.tokens_used} tokens"
            )
            
            return formatted_text
            
        except Exception as e:
            raise ProcessingError(
                f"Formatting failed: {str(e)}",
                stage="format"
            )
    
    def post_process_formatting(
        self,
        text: str,
        preferences: Dict[str, bool]
    ) -> str:
        """
        Post-process formatted text.
        
        Args:
            text: Formatted text
            preferences: Formatting preferences
            
        Returns:
            Cleaned text
        """
        # Remove any markdown code fences from wrapping
        if text.startswith("```markdown\n"):
            text = text[12:]
        if text.endswith("\n```"):
            text = text[:-4]
        
        # Ensure proper spacing
        text = self._normalize_spacing(text)
        
        # Add key concepts section if preference is set
        if preferences.get("highlight_key_concepts", True):
            text = self._ensure_key_concepts_section(text)
        
        # Add summary if preference is set
        if preferences.get("include_summaries", True):
            text = self._ensure_summary_section(text)
        
        return text.strip()
    
    def _normalize_spacing(self, text: str) -> str:
        """Normalize spacing in text."""
        # Remove multiple blank lines
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        
        # Ensure space after list markers
        text = re.sub(r'^(-|\*|\d+\.)\s*(\S)', r'\1 \2', text, flags=re.MULTILINE)
        
        # Ensure blank line before headings
        text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
        
        # Ensure blank line after headings
        text = re.sub(r'(#{1,6}\s.+)\n([^#\n])', r'\1\n\n\2', text)
        
        return text
    
    def _ensure_key_concepts_section(self, text: str) -> str:
        """Ensure text has a key concepts section."""
        # Check if already has one
        if "## Key Concepts" in text or "# Key Concepts" in text:
            return text
        
        # Extract bold terms as key concepts
        bold_terms = re.findall(r'\*\*(.+?)\*\*', text)
        
        if bold_terms and len(bold_terms) >= 2:
            # Create key concepts section
            concepts_section = "\n## Key Concepts\n\n"
            for term in bold_terms[:5]:  # Max 5 concepts
                concepts_section += f"- **{term}**\n"
            
            # Insert after first heading
            parts = text.split("\n## ", 1)
            if len(parts) == 2:
                text = parts[0] + concepts_section + "\n## " + parts[1]
            else:
                # Insert at beginning
                text = concepts_section + "\n\n" + text
        
        return text
    
    def _ensure_summary_section(self, text: str) -> str:
        """Ensure text has a summary section."""
        # Check if already has one
        if "## Summary" in text or "# Summary" in text:
            return text
        
        # If text is too short, don't add summary
        if len(text.split()) < 100:
            return text
        
        # Add placeholder for summary at the end
        summary_section = "\n\n## Summary\n\n*[Summary to be generated]*\n"
        return text + summary_section
    
    def clean_markdown(self, text: str) -> str:
        """
        Clean up markdown formatting issues.
        
        Args:
            text: Markdown text
            
        Returns:
            Cleaned text
        """
        # Fix broken lists
        text = re.sub(r'\n-\s*\n-', r'\n-', text)
        
        # Fix heading formatting
        text = re.sub(r'^#+([^\s])', r'# \1', text, flags=re.MULTILINE)
        
        # Fix bold/italic spacing
        text = re.sub(r'\*\*\s+', r'**', text)
        text = re.sub(r'\s+\*\*', r'**', text)
        
        # Fix code blocks
        text = re.sub(r'```\s*\n\s*```', '', text)
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def add_metadata_header(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Add metadata header to notes.
        
        Args:
            text: Note content
            metadata: Metadata dictionary
            
        Returns:
            Text with metadata header
        """
        header = "---\n"
        
        for key, value in metadata.items():
            if isinstance(value, list):
                header += f"{key}: {', '.join(str(v) for v in value)}\n"
            else:
                header += f"{key}: {value}\n"
        
        header += "---\n\n"
        
        return header + text
    
    def create_table_of_contents(self, text: str) -> str:
        """
        Create a table of contents from headings.
        
        Args:
            text: Markdown text
            
        Returns:
            Table of contents markdown
        """
        # Extract headings
        headings = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        
        if not headings or len(headings) < 3:
            return ""
        
        toc = "## Table of Contents\n\n"
        
        for level_str, title in headings[1:]:  # Skip main title
            level = len(level_str)
            indent = "  " * (level - 2)
            
            # Create anchor link
            anchor = title.lower().replace(" ", "-")
            anchor = re.sub(r'[^\w-]', '', anchor)
            
            toc += f"{indent}- [{title}](#{anchor})\n"
        
        return toc + "\n"
    
    def wrap_with_callouts(
        self,
        text: str,
        callout_type: str = "note"
    ) -> str:
        """
        Wrap important sections with callouts.
        
        Args:
            text: Text to wrap
            callout_type: Type of callout (note, warning, tip, important)
            
        Returns:
            Text with callouts
        """
        # Find sections marked as important
        important_pattern = r'(?:Important|Note|Warning|Tip):\s*(.+?)(?=\n\n|\Z)'
        
        def replace_with_callout(match):
            content = match.group(1)
            emoji = {
                "note": "📝",
                "warning": "⚠️",
                "tip": "💡",
                "important": "❗"
            }.get(callout_type, "📝")
            
            return f"\n> {emoji} **{callout_type.title()}**: {content}\n"
        
        text = re.sub(important_pattern, replace_with_callout, text, flags=re.DOTALL)
        
        return text
    
    def format_code_blocks(self, text: str) -> str:
        """
        Ensure code blocks are properly formatted.
        
        Args:
            text: Text with code blocks
            
        Returns:
            Text with formatted code blocks
        """
        # Find code blocks and ensure language is specified
        def add_language(match):
            code = match.group(1)
            
            # Try to detect language
            if "def " in code or "import " in code:
                lang = "python"
            elif "function " in code or "const " in code:
                lang = "javascript"
            elif "#include" in code:
                lang = "cpp"
            else:
                lang = "text"
            
            return f"```{lang}\n{code}\n```"
        
        # Match code blocks without language
        text = re.sub(r'```\n(.+?)\n```', add_language, text, flags=re.DOTALL)
        
        return text
    
    def format_math_equations(self, text: str) -> str:
        """
        Ensure math equations are properly formatted.
        
        Args:
            text: Text with math equations
            
        Returns:
            Text with formatted equations
        """
        # Ensure display math has proper delimiters
        text = re.sub(r'(?<!\$)\$\$(?!\$)', r'$$', text)
        
        # Ensure inline math has proper delimiters
        text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', r'$\1$', text)
        
        return text
    
    def validate_markdown(self, text: str) -> Dict[str, Any]:
        """
        Validate markdown formatting.
        
        Args:
            text: Markdown text
            
        Returns:
            Validation results
        """
        issues = []
        
        # Check for unmatched bold/italic
        if text.count("**") % 2 != 0:
            issues.append("Unmatched bold markers (**)")
        
        if text.count("*") % 2 != 0:
            issues.append("Unmatched italic markers (*)")
        
        # Check for unclosed code blocks
        if text.count("```") % 2 != 0:
            issues.append("Unclosed code block")
        
        # Check for proper heading hierarchy
        headings = re.findall(r'^(#{1,6})', text, re.MULTILINE)
        if headings:
            levels = [len(h) for h in headings]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    issues.append(f"Heading hierarchy skip at line {i}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "has_headings": bool(headings),
            "has_lists": "-" in text or "*" in text,
            "has_code": "```" in text,
            "has_math": "$" in text,
        }