"""
Subject-specific analysis and prioritization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SubjectAnalyzer:
    """Analyzes subjects and determines study priorities."""
    
    def __init__(self):
        """Initialize subject analyzer."""
        self.subject_weights = {
            "frequency": 0.3,
            "recency": 0.3,
            "difficulty": 0.2,
            "coverage": 0.2,
        }
        
        logger.info("Subject analyzer initialized")
    
    def analyze_subjects(
        self,
        notes: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze subjects from notes.
        
        Args:
            notes: List of note metadata
            preferences: User subject preferences
            
        Returns:
            Subject analysis
        """
        logger.info(f"Analyzing {len(notes)} notes across subjects")
        
        # Group notes by subject
        subject_notes = defaultdict(list)
        for note in notes:
            subject = note.get("subject", "Unknown")
            subject_notes[subject].append(note)
        
        # Analyze each subject
        analysis = {}
        for subject, subject_note_list in subject_notes.items():
            analysis[subject] = self._analyze_single_subject(
                subject,
                subject_note_list,
                preferences
            )
        
        # Calculate priorities
        analysis = self._calculate_priorities(analysis)
        
        return analysis
    
    def _analyze_single_subject(
        self,
        subject: str,
        notes: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze a single subject.
        
        Args:
            subject: Subject name
            notes: Notes for this subject
            preferences: User preferences
            
        Returns:
            Subject analysis
        """
        # Get preferences for this subject
        subject_pref = (preferences or {}).get(subject, {}) if preferences else {}
        
        # Calculate metrics
        note_count = len(notes)
        
        # Most recent note date
        most_recent = self._get_most_recent_date(notes)
        days_since_study = (datetime.now() - most_recent).days if most_recent else 999
        
        # Topic coverage
        topics = set()
        for note in notes:
            topics.update(note.get("topics", []))
        
        # Difficulty distribution
        difficulties = [note.get("difficulty", "Medium") for note in notes]
        difficulty_score = self._calculate_difficulty_score(difficulties)
        
        # Engagement score (based on note count and recency)
        engagement = self._calculate_engagement_score(note_count, days_since_study)
        
        return {
            "note_count": note_count,
            "days_since_study": days_since_study,
            "topic_count": len(topics),
            "topics": list(topics),
            "difficulty_score": difficulty_score,
            "engagement_score": engagement,
            "user_priority": subject_pref.get("priority", "medium"),
            "user_difficulty": subject_pref.get("difficulty", "medium"),
            "weekly_hours": subject_pref.get("weekly_hours", 3),
        }
    
    def _get_most_recent_date(self, notes: List[Dict[str, Any]]) -> Optional[datetime]:
        """Get most recent note date."""
        dates = []
        for note in notes:
            date_str = note.get("date")
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str))
                except:
                    pass
        
        return max(dates) if dates else None
    
    def _calculate_difficulty_score(self, difficulties: List[str]) -> float:
        """
        Calculate difficulty score from difficulty distribution.
        
        Args:
            difficulties: List of difficulty values
            
        Returns:
            Score from 0.0 to 1.0
        """
        if not difficulties:
            return 0.5
        
        difficulty_values = {
            "Easy": 0.3,
            "Medium": 0.5,
            "Hard": 0.8,
        }
        
        scores = [difficulty_values.get(d, 0.5) for d in difficulties]
        return sum(scores) / len(scores)
    
    def _calculate_engagement_score(
        self,
        note_count: int,
        days_since_study: int
    ) -> float:
        """
        Calculate engagement score.
        
        Args:
            note_count: Number of notes
            days_since_study: Days since last study
            
        Returns:
            Score from 0.0 to 1.0
        """
        # Frequency component (more notes = higher engagement)
        frequency_score = min(note_count / 10, 1.0)
        
        # Recency component (more recent = higher engagement)
        recency_score = max(0, 1.0 - (days_since_study / 30))
        
        return (frequency_score + recency_score) / 2
    
    def _calculate_priorities(
        self,
        analysis: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate priority scores for subjects.
        
        Args:
            analysis: Subject analysis
            
        Returns:
            Updated analysis with priorities
        """
        for subject, data in analysis.items():
            # Factors
            frequency_score = min(data["note_count"] / 10, 1.0)
            recency_score = max(0, 1.0 - (data["days_since_study"] / 30))
            difficulty_score = data["difficulty_score"]
            coverage_score = min(data["topic_count"] / 10, 1.0)
            
            # User priority boost
            priority_boost = {
                "low": 0.8,
                "medium": 1.0,
                "high": 1.3,
            }.get(data["user_priority"], 1.0)
            
            # Calculate weighted score
            priority_score = (
                frequency_score * self.subject_weights["frequency"] +
                recency_score * self.subject_weights["recency"] +
                difficulty_score * self.subject_weights["difficulty"] +
                coverage_score * self.subject_weights["coverage"]
            ) * priority_boost
            
            data["priority_score"] = priority_score
            
            # Determine if needs attention
            data["needs_attention"] = (
                data["days_since_study"] > 7 or
                data["difficulty_score"] > 0.6
            )
        
        return analysis
    
    def get_priority_ranking(
        self,
        analysis: Dict[str, Dict[str, Any]]
    ) -> List[tuple[str, float]]:
        """
        Get subjects ranked by priority.
        
        Args:
            analysis: Subject analysis
            
        Returns:
            List of (subject, priority_score) tuples
        """
        ranking = [
            (subject, data["priority_score"])
            for subject, data in analysis.items()
        ]
        
        return sorted(ranking, key=lambda x: x[1], reverse=True)
    
    def get_subjects_needing_attention(
        self,
        analysis: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """
        Get subjects that need attention.
        
        Args:
            analysis: Subject analysis
            
        Returns:
            List of subject names
        """
        return [
            subject
            for subject, data in analysis.items()
            if data.get("needs_attention", False)
        ]
    
    def suggest_study_distribution(
        self,
        analysis: Dict[str, Dict[str, Any]],
        total_hours: float,
    ) -> Dict[str, float]:
        """
        Suggest time distribution across subjects.
        
        Args:
            analysis: Subject analysis
            total_hours: Total available hours
            
        Returns:
            Dictionary of subject: hours
        """
        # Get priority ranking
        ranking = self.get_priority_ranking(analysis)
        
        # Calculate proportional distribution
        total_priority = sum(score for _, score in ranking)
        
        if total_priority == 0:
            # Equal distribution
            hours_per_subject = total_hours / len(ranking)
            return {subject: hours_per_subject for subject, _ in ranking}
        
        distribution = {}
        for subject, priority_score in ranking:
            proportion = priority_score / total_priority
            distribution[subject] = round(total_hours * proportion, 1)
        
        return distribution
    
    def get_recommended_topics(
        self,
        subject: str,
        analysis: Dict[str, Dict[str, Any]],
        max_topics: int = 5,
    ) -> List[str]:
        """
        Get recommended topics to review for a subject.
        
        Args:
            subject: Subject name
            analysis: Subject analysis
            max_topics: Maximum topics to return
            
        Returns:
            List of topic names
        """
        subject_data = analysis.get(subject, {})
        topics = subject_data.get("topics", [])
        
        # For now, return all topics (could be enhanced with topic-level analysis)
        return topics[:max_topics]
    
    def compare_to_goals(
        self,
        analysis: Dict[str, Dict[str, Any]],
        goals: Dict[str, float],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare actual study time to goals.
        
        Args:
            analysis: Subject analysis
            goals: Goal hours per subject per week
            
        Returns:
            Comparison results
        """
        comparison = {}
        
        for subject, goal_hours in goals.items():
            subject_data = analysis.get(subject, {})
            actual_notes = subject_data.get("note_count", 0)
            
            # Rough estimate: 1 note ≈ 1 hour of study
            estimated_hours = actual_notes
            
            comparison[subject] = {
                "goal_hours": goal_hours,
                "estimated_hours": estimated_hours,
                "difference": estimated_hours - goal_hours,
                "on_track": estimated_hours >= goal_hours * 0.8,
            }
        
        return comparison