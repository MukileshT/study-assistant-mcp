"""
Learning optimization and spaced repetition.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReviewSession:
    """Represents a recommended review session."""
    
    subject: str
    topics: List[str]
    suggested_date: datetime
    priority: int  # 1-5, higher is more urgent
    interval_days: int
    reason: str


class LearningOptimizer:
    """Optimizes learning using spaced repetition and learning science."""
    
    def __init__(self):
        """Initialize learning optimizer."""
        # Spaced repetition intervals (in days)
        self.review_intervals = [1, 3, 7, 14, 30, 60]
        
        # Learning style strategies
        self.learning_strategies = {
            "visual": {
                "techniques": [
                    "Create diagrams and mind maps",
                    "Use color coding",
                    "Watch video explanations",
                    "Draw concept relationships",
                ],
                "study_methods": ["visual mapping", "diagram creation", "video review"],
            },
            "auditory": {
                "techniques": [
                    "Explain concepts out loud",
                    "Discuss with study groups",
                    "Record and listen to summaries",
                    "Use mnemonics and rhymes",
                ],
                "study_methods": ["verbal explanation", "group discussion", "audio review"],
            },
            "kinesthetic": {
                "techniques": [
                    "Work through practice problems",
                    "Build physical models",
                    "Take breaks with movement",
                    "Use flashcards actively",
                ],
                "study_methods": ["hands-on practice", "problem solving", "active recall"],
            },
            "reading_writing": {
                "techniques": [
                    "Rewrite notes in your own words",
                    "Create detailed outlines",
                    "Write practice essays",
                    "Make comprehensive lists",
                ],
                "study_methods": ["note rewriting", "outline creation", "written summaries"],
            },
        }
        
        logger.info("Learning optimizer initialized")
    
    def calculate_review_schedule(
        self,
        notes: List[Dict[str, Any]],
        current_date: datetime,
    ) -> List[ReviewSession]:
        """
        Calculate optimal review schedule using spaced repetition.
        
        Args:
            notes: List of notes with dates
            current_date: Current date
            
        Returns:
            List of recommended review sessions
        """
        logger.info("Calculating review schedule with spaced repetition")
        
        review_sessions = []
        
        # Group notes by subject
        subject_notes = {}
        for note in notes:
            subject = note.get("subject", "Unknown")
            if subject not in subject_notes:
                subject_notes[subject] = []
            subject_notes[subject].append(note)
        
        # Calculate reviews for each subject
        for subject, subject_note_list in subject_notes.items():
            sessions = self._calculate_subject_reviews(
                subject,
                subject_note_list,
                current_date
            )
            review_sessions.extend(sessions)
        
        # Sort by priority and date
        review_sessions.sort(key=lambda x: (x.suggested_date, -x.priority))
        
        logger.info(f"Generated {len(review_sessions)} review sessions")
        return review_sessions
    
    def _calculate_subject_reviews(
        self,
        subject: str,
        notes: List[Dict[str, Any]],
        current_date: datetime,
    ) -> List[ReviewSession]:
        """Calculate reviews for a single subject."""
        sessions = []
        
        for note in notes:
            date_str = note.get("date")
            if not date_str:
                continue
            
            try:
                note_date = datetime.fromisoformat(date_str)
            except:
                continue
            
            days_since = (current_date - note_date).days
            
            # Determine which review interval we're in
            next_review = self._get_next_review_interval(days_since)
            
            if next_review is not None:
                suggested_date = note_date + timedelta(days=next_review)
                
                # Only include if due soon (within 3 days)
                if (suggested_date - current_date).days <= 3:
                    priority = self._calculate_review_priority(
                        days_since,
                        next_review,
                        note.get("difficulty", "Medium")
                    )
                    
                    sessions.append(ReviewSession(
                        subject=subject,
                        topics=note.get("topics", []),
                        suggested_date=suggested_date,
                        priority=priority,
                        interval_days=next_review,
                        reason=self._get_review_reason(days_since, next_review)
                    ))
        
        return sessions
    
    def _get_next_review_interval(self, days_since: int) -> Optional[int]:
        """Get the next review interval based on days since last study."""
        for interval in self.review_intervals:
            if days_since <= interval:
                return interval
        return None
    
    def _calculate_review_priority(
        self,
        days_since: int,
        interval: int,
        difficulty: str,
    ) -> int:
        """
        Calculate review priority (1-5).
        
        Args:
            days_since: Days since last study
            interval: Recommended interval
            difficulty: Note difficulty
            
        Returns:
            Priority from 1 to 5
        """
        # Base priority on how overdue the review is
        overdue_ratio = days_since / interval
        
        if overdue_ratio >= 1.0:
            base_priority = 5
        elif overdue_ratio >= 0.9:
            base_priority = 4
        elif overdue_ratio >= 0.7:
            base_priority = 3
        elif overdue_ratio >= 0.5:
            base_priority = 2
        else:
            base_priority = 1
        
        # Boost priority for difficult content
        if difficulty == "Hard":
            base_priority = min(5, base_priority + 1)
        
        return base_priority
    
    def _get_review_reason(self, days_since: int, interval: int) -> str:
        """Get explanation for why review is recommended."""
        overdue_ratio = days_since / interval
        
        if overdue_ratio >= 1.0:
            return f"Overdue review (studied {days_since} days ago)"
        elif overdue_ratio >= 0.9:
            return f"Due for review (studied {days_since} days ago)"
        else:
            return f"Approaching review time (studied {days_since} days ago)"
    
    def optimize_study_session(
        self,
        duration_minutes: int,
        learning_style: str,
        subject: str,
    ) -> Dict[str, Any]:
        """
        Optimize a study session structure.
        
        Args:
            duration_minutes: Total session duration
            learning_style: User's learning style
            subject: Subject being studied
            
        Returns:
            Optimized session plan
        """
        # Get learning strategies for style
        strategies = self.learning_strategies.get(
            learning_style,
            self.learning_strategies["visual"]
        )
        
        # Optimal session structure (research-based)
        if duration_minutes <= 30:
            # Short session - no break needed
            structure = {
                "total_minutes": duration_minutes,
                "segments": [
                    {"type": "review", "minutes": duration_minutes * 0.2},
                    {"type": "new_content", "minutes": duration_minutes * 0.6},
                    {"type": "practice", "minutes": duration_minutes * 0.2},
                ],
                "breaks": [],
            }
        else:
            # Longer session - include breaks (Pomodoro-style)
            work_blocks = duration_minutes // 25
            break_minutes = (work_blocks - 1) * 5
            
            structure = {
                "total_minutes": duration_minutes,
                "segments": [
                    {"type": "review", "minutes": 10},
                    {"type": "new_content", "minutes": duration_minutes * 0.5},
                    {"type": "practice", "minutes": duration_minutes * 0.3},
                    {"type": "review", "minutes": duration_minutes * 0.2},
                ],
                "breaks": [
                    {"after_minutes": 25, "duration": 5}
                    for _ in range(work_blocks - 1)
                ],
            }
        
        return {
            "structure": structure,
            "recommended_techniques": strategies["techniques"],
            "study_methods": strategies["study_methods"],
            "learning_style": learning_style,
        }
    
    def suggest_study_techniques(
        self,
        learning_style: str,
        subject: str,
        difficulty: str,
    ) -> List[str]:
        """
        Suggest study techniques based on learning style and difficulty.
        
        Args:
            learning_style: User's learning style
            subject: Subject name
            difficulty: Content difficulty
            
        Returns:
            List of recommended techniques
        """
        strategies = self.learning_strategies.get(
            learning_style,
            self.learning_strategies["visual"]
        )
        
        techniques = strategies["techniques"].copy()
        
        # Add difficulty-specific techniques
        if difficulty == "Hard":
            techniques.extend([
                "Break down into smaller concepts",
                "Find analogies and examples",
                "Teach it to someone else",
            ])
        
        # Add subject-specific techniques
        if "math" in subject.lower():
            techniques.extend([
                "Work through many practice problems",
                "Understand the process, not just memorize",
            ])
        elif "science" in subject.lower():
            techniques.extend([
                "Connect concepts to real-world examples",
                "Draw diagrams of processes",
            ])
        
        return techniques
    
    def calculate_retention_probability(
        self,
        days_since_study: int,
        review_count: int,
        difficulty: str,
    ) -> float:
        """
        Calculate estimated retention probability (Ebbinghaus forgetting curve).
        
        Args:
            days_since_study: Days since last study
            review_count: Number of times reviewed
            difficulty: Content difficulty
            
        Returns:
            Retention probability (0.0 to 1.0)
        """
        # Base forgetting curve: R = e^(-t/S)
        # S = strength, increases with reviews
        
        difficulty_factor = {
            "Easy": 1.2,
            "Medium": 1.0,
            "Hard": 0.7,
        }.get(difficulty, 1.0)
        
        # Strength increases with each review
        strength = 5 * (1 + review_count) * difficulty_factor
        
        # Calculate retention
        retention = math.exp(-days_since_study / strength)
        
        return min(1.0, max(0.0, retention))
    
    def recommend_interleaving(
        self,
        subjects: List[str],
        session_count: int,
    ) -> List[str]:
        """
        Recommend interleaved subject order for better learning.
        
        Args:
            subjects: List of subjects to study
            session_count: Number of study sessions
            
        Returns:
            Ordered list of subjects (interleaved)
        """
        if len(subjects) <= 1:
            return subjects * session_count
        
        # Interleave subjects to avoid massed practice
        interleaved = []
        for i in range(session_count):
            # Rotate through subjects
            subject_index = i % len(subjects)
            interleaved.append(subjects[subject_index])
        
        return interleaved
    
    def calculate_cognitive_load(
        self,
        tasks: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate cognitive load for a set of tasks.
        
        Args:
            tasks: List of tasks with difficulty and duration
            
        Returns:
            Cognitive load score (0.0 to 1.0)
        """
        if not tasks:
            return 0.0
        
        total_load = 0
        total_time = 0
        
        difficulty_weights = {
            "Easy": 0.3,
            "Medium": 0.6,
            "Hard": 1.0,
        }
        
        for task in tasks:
            difficulty = task.get("difficulty", "Medium")
            duration = task.get("duration_minutes", 30)
            
            weight = difficulty_weights.get(difficulty, 0.6)
            total_load += weight * duration
            total_time += duration
        
        # Normalize by total time
        if total_time > 0:
            return min(1.0, total_load / (total_time * 0.8))
        
        return 0.0