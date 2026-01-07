"""
Reusable prompt templates for various tasks.
"""

from typing import Dict, List, Optional
from datetime import datetime


class PromptTemplates:
    """Collection of prompt templates for different tasks."""
    
    @staticmethod
    def ocr_extraction_prompt(
        detail_level: str = "standard",
        include_diagrams: bool = True,
    ) -> str:
        """
        Generate prompt for OCR extraction.
        
        Args:
            detail_level: Level of detail (minimal, standard, detailed)
            include_diagrams: Whether to extract diagram descriptions
            
        Returns:
            OCR extraction prompt
        """
        base_prompt = """Extract all text from this handwritten note image. Follow these guidelines:

1. **Accuracy**: Transcribe exactly what you see, maintaining original wording
2. **Structure**: Preserve the hierarchical structure (headings, subheadings, bullets)
3. **Formatting**: Use markdown for structure:
   - Use # for main headings, ## for subheadings, ### for sub-subheadings
   - Use - for bullet points
   - Use 1. 2. 3. for numbered lists
4. **Special Content**:
   - Formulas: Use LaTeX notation in $ $ for inline or $$ $$ for display
   - Code: Use ```language for code blocks
   - Tables: Use markdown table syntax"""
        
        if include_diagrams:
            base_prompt += """
5. **Diagrams**: Describe any diagrams, charts, or drawings in [DIAGRAM: description] format"""
        
        if detail_level == "minimal":
            base_prompt += """

Focus on main points and key information only. Skip redundant examples."""
        elif detail_level == "detailed":
            base_prompt += """

Include ALL details, examples, side notes, and annotations. Don't skip anything."""
        
        base_prompt += """

6. **Unclear Text**: Mark unclear or illegible text as [UNCLEAR: best guess]

Output only the extracted text in markdown format. Do not add commentary or explanations."""
        
        return base_prompt
    
    @staticmethod
    def content_analysis_prompt(
        learning_style: str = "visual",
    ) -> str:
        """
        Generate prompt for content analysis.
        
        Args:
            learning_style: User's learning style
            
        Returns:
            Content analysis prompt
        """
        base_prompt = """Analyze this note content and provide a structured analysis:

1. **Key Concepts** (3-5 main concepts):
   - List the most important concepts covered
   - Brief explanation of each

2. **Main Topics**:
   - Primary topics
   - Subtopics

3. **Important Details**:
   - Critical facts, formulas, or definitions
   - Things that are likely exam material

4. **Relationships**:
   - How concepts relate to each other
   - Dependencies or prerequisites

5. **Summary**:
   - 2-3 sentence overview of the content"""
        
        if learning_style == "visual":
            base_prompt += """

6. **Visual Elements**:
   - Suggest diagrams or charts that would help understanding
   - Recommend visual study aids"""
        elif learning_style == "auditory":
            base_prompt += """

6. **Discussion Points**:
   - Questions to discuss with study group
   - Key points to explain out loud"""
        elif learning_style == "kinesthetic":
            base_prompt += """

6. **Practice Activities**:
   - Hands-on exercises to try
   - Real-world applications"""
        elif learning_style == "reading_writing":
            base_prompt += """

6. **Additional Reading**:
   - Topics to research further
   - Writing prompts to deepen understanding"""
        
        base_prompt += """

Format your analysis in clear sections with markdown."""
        
        return base_prompt
    
    @staticmethod
    def formatting_prompt(
        style_preferences: Optional[Dict[str, bool]] = None,
    ) -> str:
        """
        Generate prompt for note formatting.
        
        Args:
            style_preferences: Formatting preferences
            
        Returns:
            Formatting prompt
        """
        prefs = style_preferences or {}
        
        prompt = """Format these notes into clean, well-structured markdown. Apply these rules:

1. **Hierarchy**:
   - Use # for course/lecture title
   - Use ## for main sections
   - Use ### for subsections

2. **Lists**:
   - Use - for unordered lists
   - Use 1. 2. 3. for ordered/sequential lists
   - Indent nested lists properly

3. **Emphasis**:
   - **Bold** for key terms and important concepts
   - *Italic* for emphasis or definitions
   - `Code` for technical terms or commands

4. **Special Blocks**:
   - > for important quotes or theorems
   - ```language for code examples
   - --- for section dividers"""
        
        if prefs.get("use_emojis", True):
            prompt += """

5. **Emojis** (use sparingly for visual markers):
   - 📝 for definitions
   - ⚠️ for important warnings
   - 💡 for key insights
   - ✅ for completed examples
   - ❓ for questions to review"""
        
        if prefs.get("highlight_key_concepts", True):
            prompt += """

6. **Highlighting**:
   - Create a "Key Concepts" section at the top
   - Use callout boxes (> **Key Concept**: ...) for critical ideas"""
        
        if prefs.get("include_summaries", True):
            prompt += """

7. **Summary Section**:
   - Add a "Summary" section at the end
   - 3-5 bullet points of main takeaways"""
        
        prompt += """

Output the formatted markdown. Maintain all content but improve structure and readability."""
        
        return prompt
    
    @staticmethod
    def study_plan_prompt(
        recent_notes: List[Dict[str, str]],
        user_preferences: Dict[str, any],
        target_date: datetime,
    ) -> str:
        """
        Generate prompt for study plan creation.
        
        Args:
            recent_notes: List of recent note metadata
            user_preferences: User study preferences
            target_date: Date for the study plan
            
        Returns:
            Study planning prompt
        """
        # Format recent notes
        notes_summary = "\n".join([
            f"- {note.get('subject', 'Unknown')}: {note.get('title', 'Untitled')} "
            f"(Topics: {', '.join(note.get('topics', []))})"
            for note in recent_notes[:10]
        ])
        
        learning_style = user_preferences.get("learning_style", "visual")
        max_hours = user_preferences.get("max_daily_hours", 6)
        session_duration = user_preferences.get("study_session_duration", 45)
        
        prompt = f"""Create a personalized study plan for {target_date.strftime('%A, %B %d, %Y')}.

**Recent Learning Activity:**
{notes_summary}

**Student Profile:**
- Learning Style: {learning_style}
- Available Study Time: {max_hours} hours
- Preferred Session Length: {session_duration} minutes
- Study Pace: {user_preferences.get('study_pace', 'moderate')}

**Requirements:**
1. Analyze which subjects need the most attention based on:
   - Recency (what was studied recently)
   - Complexity (difficult topics need more time)
   - Gaps (areas not recently covered)
   - Upcoming priorities

2. Create a balanced daily schedule that:
   - Distributes time across 2-4 subjects
   - Uses spaced repetition principles
   - Includes breaks (10-15 min between sessions)
   - Matches the student's learning style
   - Stays within {max_hours} hours total

3. For each study block, specify:
   - Subject and specific topics to review
   - Recommended study method (read, practice, review notes, etc.)
   - Time allocation
   - Specific goals/outcomes

4. Provide:
   - Morning schedule (high-energy tasks)
   - Afternoon schedule (moderate tasks)
   - Evening schedule (review/lighter tasks)

**Format:**
```markdown
# Study Plan - [Date]

## Priority Subjects
[List 2-4 subjects with rationale]

## Schedule

### Morning (9:00 AM - 12:00 PM)
**Session 1: [Subject] (9:00-9:45)**
- Topics: [specific topics]
- Method: [study method]
- Goal: [specific outcome]

[Continue for each session]

### Afternoon (2:00 PM - 5:00 PM)
[Similar structure]

### Evening (7:00 PM - 9:00 PM)
[Similar structure]

## Study Tips for Today
- [3-5 personalized tips based on learning style]

## Expected Outcomes
- [What should be accomplished by end of day]
```

Create a realistic, achievable plan that maximizes learning effectiveness."""
        
        return prompt
    
    @staticmethod
    def topic_extraction_prompt() -> str:
        """Generate prompt for extracting topics from notes."""
        return """Analyze this note and extract the main topics covered.

Requirements:
1. Identify 3-8 specific topics (not too broad, not too narrow)
2. Use clear, searchable topic names
3. Focus on content themes, not structure (e.g., "Photosynthesis" not "Introduction")
4. Use standard terminology when possible

Examples:
- Good: "Quadratic Equations", "Photosynthesis", "World War II Causes"
- Bad: "Chapter 3", "Introduction", "Conclusion"

Output format:
Return ONLY a JSON array of topic strings, nothing else:
["Topic 1", "Topic 2", "Topic 3"]"""
    
    @staticmethod
    def subject_classification_prompt(available_subjects: List[str]) -> str:
        """
        Generate prompt for subject classification.
        
        Args:
            available_subjects: List of possible subjects
            
        Returns:
            Classification prompt
        """
        subjects_list = ", ".join(available_subjects)
        
        return f"""Classify this note into ONE of the following subjects:
{subjects_list}

Guidelines:
1. Choose the most specific subject that fits
2. If uncertain between two subjects, choose the primary focus
3. If none fit well, choose "Other"

Output format:
Return ONLY the subject name, nothing else. Example: "Mathematics" """
    
    @staticmethod
    def difficulty_assessment_prompt() -> str:
        """Generate prompt for assessing difficulty."""
        return """Assess the difficulty level of this content.

Consider:
1. Complexity of concepts
2. Prerequisites needed
3. Level of abstraction
4. Technical depth

Classify as:
- **Easy**: Basic concepts, minimal prerequisites, concrete examples
- **Medium**: Moderate complexity, some prerequisites, mix of concrete and abstract
- **Hard**: Advanced concepts, significant prerequisites, highly abstract

Output format:
Return ONLY one word: Easy, Medium, or Hard"""
    
    @staticmethod
    def summary_generation_prompt(max_sentences: int = 3) -> str:
        """
        Generate prompt for creating summaries.
        
        Args:
            max_sentences: Maximum number of sentences
            
        Returns:
            Summary prompt
        """
        return f"""Create a concise summary of this content in {max_sentences} sentences or less.

Requirements:
1. Capture the main points and key takeaways
2. Use clear, direct language
3. Focus on what's most important
4. Make it useful for quick review

Output the summary directly, no preamble."""
    
    @staticmethod
    def question_generation_prompt(num_questions: int = 5) -> str:
        """
        Generate prompt for creating study questions.
        
        Args:
            num_questions: Number of questions to generate
            
        Returns:
            Question generation prompt
        """
        return f"""Generate {num_questions} study questions based on this content.

Requirements:
1. Mix of question types:
   - Recall questions (test memory)
   - Application questions (test understanding)
   - Analysis questions (test deeper thinking)

2. Questions should:
   - Be clear and specific
   - Cover different topics in the content
   - Be answerable from the content
   - Progress from easy to challenging

Format as a numbered list:
1. [Question]
2. [Question]
..."""