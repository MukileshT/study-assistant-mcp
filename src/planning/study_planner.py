"""
Study plan generation and scheduling.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from src.models import ModelManager
from src.storage import NotionClient, DatabaseManager
from src.utils.logger import get_logger
from src.utils.error_handlers import ProcessingError
from src.utils.prompt_templates import PromptTemplates
from config.settings import get_settings

logger = get_logger(__name__)


class StudyPlanner:
    """Generates personalized study plans."""
    
    def __init__(self):
        """Initialize study planner."""
        self.model_manager = ModelManager()
        self.notion_client = NotionClient()
        self.db_manager = DatabaseManager()
        self.settings = get_settings()
        self.prompt_templates = PromptTemplates()
        
        # Load user preferences
        self.load_preferences()
        
        logger.info("Study planner initialized")
    
    def load_preferences(self):
        """Load planning preferences from config."""
        try:
            prefs_path = Path("config/user_preferences.json")
            if prefs_path.exists():
                with open(prefs_path, 'r') as f:
                    data = json.load(f)
                    self.user_prefs = data.get("planning_preferences", {})
                    self.subject_prefs = data.get("subject_preferences", {})
                    self.learning_style = data.get("user_profile", {}).get(
                        "learning_style", "visual"
                    )
            else:
                self._set_default_preferences()
        except Exception as e:
            logger.warning(f"Could not load preferences: {str(e)}")
            self._set_default_preferences()
    
    def _set_default_preferences(self):
        """Set default preferences."""
        self.user_prefs = {
            "study_session_duration": 45,
            "break_duration": 10,
            "max_daily_hours": 6,
            "preferred_subjects_per_day": 3,
        }
        self.subject_prefs = {}
        self.learning_style = self.settings.learning_style
    
    async def generate_daily_plan(
        self,
        target_date: datetime,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a daily study plan.
        
        Args:
            target_date: Date for the plan
            force_regenerate: Force regeneration even if plan exists
            
        Returns:
            Generated plan
        """
        logger.info(f"Generating study plan for {target_date.date()}")
        
        # Check if plan already exists
        if not force_regenerate:
            existing_plan = await self.db_manager.get_study_plan(target_date)
            if existing_plan:
                logger.info("Plan already exists, using cached version")
                return existing_plan
        
        try:
            # Gather recent notes
            recent_notes = await self._gather_recent_notes(days=14)
            
            if not recent_notes:
                logger.warning("No recent notes found for planning")
                return self._generate_default_plan(target_date)
            
            # Analyze learning patterns
            analysis = await self._analyze_learning_patterns(recent_notes)
            
            # Generate plan using AI
            plan_content = await self._generate_plan_with_ai(
                target_date,
                recent_notes,
                analysis
            )
            
            # Structure the plan
            structured_plan = self._structure_plan(plan_content, analysis)
            
            # Upload to Notion
            notion_page_id = await self._upload_plan_to_notion(
                target_date,
                plan_content,
                structured_plan
            )
            
            # Save to database
            await self.db_manager.save_study_plan(
                date=target_date,
                notion_page_id=notion_page_id,
                priority_subjects=structured_plan["priority_subjects"],
                total_hours=structured_plan["total_hours"],
                metadata=structured_plan
            )
            
            logger.info("Study plan generated successfully")
            
            return {
                "success": True,
                "date": target_date.date().isoformat(),
                "notion_page_id": notion_page_id,
                "priority_subjects": structured_plan["priority_subjects"],
                "total_hours": structured_plan["total_hours"],
                "content": plan_content,
            }
            
        except Exception as e:
            logger.error(f"Plan generation failed: {str(e)}")
            raise ProcessingError(
                f"Failed to generate study plan: {str(e)}",
                stage="plan_generation"
            )
    
    async def _gather_recent_notes(self, days: int = 14) -> List[Dict[str, Any]]:
        """
        Gather recent notes from Notion.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of note metadata
        """
        try:
            pages = await self.notion_client.get_recent_notes(days=days)
            
            notes = []
            for page in pages:
                props = page.get("properties", {})
                
                # Extract properties
                title = self._extract_notion_title(props.get("Title", {}))
                subject = self._extract_notion_select(props.get("Subject", {}))
                topics = self._extract_notion_multi_select(props.get("Topics", {}))
                date_obj = self._extract_notion_date(props.get("Date", {}))
                difficulty = self._extract_notion_select(props.get("Difficulty", {}))
                
                notes.append({
                    "title": title,
                    "subject": subject,
                    "topics": topics,
                    "date": date_obj.isoformat() if date_obj else None,
                    "difficulty": difficulty,
                })
            
            logger.info(f"Gathered {len(notes)} recent notes")
            return notes
            
        except Exception as e:
            logger.warning(f"Failed to gather recent notes: {str(e)}")
            return []
    
    def _extract_notion_title(self, title_prop: Dict) -> str:
        """Extract title from Notion property."""
        title_array = title_prop.get("title", [])
        if title_array:
            return title_array[0].get("text", {}).get("content", "")
        return ""
    
    def _extract_notion_select(self, select_prop: Dict) -> str:
        """Extract select value from Notion property."""
        select = select_prop.get("select", {})
        return select.get("name", "") if select else ""
    
    def _extract_notion_multi_select(self, multi_select_prop: Dict) -> List[str]:
        """Extract multi-select values from Notion property."""
        multi_select = multi_select_prop.get("multi_select", [])
        return [item.get("name", "") for item in multi_select]
    
    def _extract_notion_date(self, date_prop: Dict) -> Optional[datetime]:
        """Extract date from Notion property."""
        date_obj = date_prop.get("date", {})
        if date_obj and date_obj.get("start"):
            try:
                return datetime.fromisoformat(date_obj["start"].replace("Z", "+00:00"))
            except:
                return None
        return None
    
    async def _analyze_learning_patterns(
        self,
        recent_notes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze learning patterns from recent notes.
        
        Args:
            recent_notes: List of recent notes
            
        Returns:
            Analysis results
        """
        # Subject frequency
        subject_count = {}
        topic_count = {}
        difficulty_count = {"Easy": 0, "Medium": 0, "Hard": 0}
        
        for note in recent_notes:
            subject = note.get("subject", "")
            if subject:
                subject_count[subject] = subject_count.get(subject, 0) + 1
            
            for topic in note.get("topics", []):
                topic_count[topic] = topic_count.get(topic, 0) + 1
            
            difficulty = note.get("difficulty", "")
            if difficulty in difficulty_count:
                difficulty_count[difficulty] += 1
        
        # Calculate days since last study per subject
        subject_last_date = {}
        for note in recent_notes:
            subject = note.get("subject", "")
            date_str = note.get("date")
            if subject and date_str:
                try:
                    note_date = datetime.fromisoformat(date_str)
                    if subject not in subject_last_date or note_date > subject_last_date[subject]:
                        subject_last_date[subject] = note_date
                except:
                    pass
        
        days_since_study = {}
        now = datetime.now()
        for subject, last_date in subject_last_date.items():
            days = (now - last_date).days
            days_since_study[subject] = days
        
        return {
            "subject_frequency": subject_count,
            "topic_frequency": topic_count,
            "difficulty_distribution": difficulty_count,
            "days_since_study": days_since_study,
            "total_notes": len(recent_notes),
        }
    
    async def _generate_plan_with_ai(
        self,
        target_date: datetime,
        recent_notes: List[Dict[str, Any]],
        analysis: Dict[str, Any],
    ) -> str:
        """
        Generate plan using AI.
        
        Args:
            target_date: Date for plan
            recent_notes: Recent notes
            analysis: Learning pattern analysis
            
        Returns:
            Generated plan content
        """
        # Generate prompt
        prompt = self.prompt_templates.study_plan_prompt(
            recent_notes=recent_notes,
            user_preferences={
                "learning_style": self.learning_style,
                "max_daily_hours": self.user_prefs.get("max_daily_hours", 6),
                "study_session_duration": self.user_prefs.get("study_session_duration", 45),
                "study_pace": "moderate",
            },
            target_date=target_date,
        )
        
        # Add analysis context
        context = f"\n\nRecent Learning Patterns:\n"
        context += f"- Most studied subjects: {', '.join(list(analysis['subject_frequency'].keys())[:3])}\n"
        context += f"- Subjects needing attention: "
        
        # Find subjects not studied recently
        neglected = [
            s for s, days in analysis["days_since_study"].items()
            if days > 5
        ]
        context += ', '.join(neglected) if neglected else "None"
        
        full_prompt = prompt + context
        
        # Generate plan
        response = await self.model_manager.generate(
            prompt=full_prompt,
            task="planning",
        )
        
        if not response.success:
            raise ProcessingError(
                f"AI plan generation failed: {response.error}",
                stage="ai_generation"
            )
        
        return response.content
    
    def _structure_plan(
        self,
        plan_content: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data from plan.
        
        Args:
            plan_content: Generated plan text
            analysis: Learning analysis
            
        Returns:
            Structured plan data
        """
        # Extract priority subjects from content
        priority_subjects = []
        
        # Look for subject mentions
        for subject in analysis["subject_frequency"].keys():
            if subject.lower() in plan_content.lower():
                priority_subjects.append(subject)
        
        # If none found, use top 3 from analysis
        if not priority_subjects:
            priority_subjects = list(analysis["subject_frequency"].keys())[:3]
        
        # Estimate total hours from content
        # Look for time mentions
        import re
        time_pattern = r'(\d+)\s*(?:hours?|hrs?)'
        times = re.findall(time_pattern, plan_content.lower())
        
        total_hours = sum(int(t) for t in times) if times else self.user_prefs.get("max_daily_hours", 6)
        
        return {
            "priority_subjects": priority_subjects,
            "total_hours": min(total_hours, self.user_prefs.get("max_daily_hours", 6)),
            "sessions_planned": len(re.findall(r'Session \d+', plan_content)),
            "analysis": analysis,
        }
    
    async def _upload_plan_to_notion(
        self,
        target_date: datetime,
        plan_content: str,
        structured_plan: Dict[str, Any],
    ) -> str:
        """
        Upload plan to Notion.
        
        Args:
            target_date: Plan date
            plan_content: Plan content
            structured_plan: Structured plan data
            
        Returns:
            Notion page ID
        """
        title = f"Study Plan - {target_date.strftime('%B %d, %Y')}"
        
        page_id = await self.notion_client.create_study_plan_page(
            title=title,
            content=plan_content,
            date=target_date,
            priority_subjects=structured_plan["priority_subjects"],
            total_hours=structured_plan["total_hours"],
        )
        
        logger.info(f"Uploaded plan to Notion: {page_id}")
        return page_id
    
    def _generate_default_plan(self, target_date: datetime) -> Dict[str, Any]:
        """
        Generate a default plan when no recent notes exist.
        
        Args:
            target_date: Date for plan
            
        Returns:
            Default plan
        """
        default_content = f"""# Study Plan - {target_date.strftime('%B %d, %Y')}

## Note
No recent notes found. Here's a general study plan.

## Morning Session (9:00 AM - 11:00 AM)
- Review previous materials
- Focus on challenging subjects
- Take organized notes

## Afternoon Session (2:00 PM - 4:00 PM)
- Practice problems
- Review concepts
- Create study aids

## Evening Review (7:00 PM - 8:00 PM)
- Quick review of the day
- Prepare for tomorrow
- Organize materials

## Tips
- Take regular breaks
- Stay hydrated
- Get enough sleep
"""
        
        return {
            "success": True,
            "date": target_date.date().isoformat(),
            "content": default_content,
            "priority_subjects": [],
            "total_hours": 4,
            "is_default": True,
        }
    
    async def get_upcoming_deadlines(self) -> List[Dict[str, Any]]:
        """
        Get upcoming deadlines and important dates.
        
        Returns:
            List of deadlines
        """
        # Placeholder for future enhancement
        # Would integrate with calendar or task management
        return []
    
    async def adjust_plan(
        self,
        date: datetime,
        adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust an existing plan.
        
        Args:
            date: Plan date
            adjustments: Adjustments to make
            
        Returns:
            Updated plan
        """
        # Get existing plan
        plan = await self.db_manager.get_study_plan(date)
        
        if not plan:
            raise ProcessingError("No plan found for this date")
        
        # Apply adjustments (placeholder)
        # In production, would update Notion and database
        
        logger.info(f"Adjusted plan for {date.date()}")
        return plan