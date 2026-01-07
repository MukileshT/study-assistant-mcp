"""
Notion page templates and database schemas.
"""

from typing import Dict, Any, List
from datetime import datetime


class NotionTemplates:
    """Templates for Notion pages and databases."""
    
    @staticmethod
    def notes_database_schema() -> Dict[str, Any]:
        """
        Schema for the main notes database.
        
        Returns:
            Database properties schema
        """
        return {
            "Title": {"title": {}},
            "Subject": {
                "select": {
                    "options": [
                        {"name": "Mathematics", "color": "blue"},
                        {"name": "Computer Science", "color": "purple"},
                        {"name": "Physics", "color": "red"},
                        {"name": "Chemistry", "color": "green"},
                        {"name": "Biology", "color": "yellow"},
                        {"name": "English", "color": "pink"},
                        {"name": "History", "color": "brown"},
                        {"name": "Other", "color": "gray"},
                    ]
                }
            },
            "Date": {"date": {}},
            "Topics": {
                "multi_select": {
                    "options": []  # Will be populated dynamically
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Processed", "color": "green"},
                        {"name": "Review", "color": "yellow"},
                        {"name": "Incomplete", "color": "red"},
                    ]
                }
            },
            "Difficulty": {
                "select": {
                    "options": [
                        {"name": "Easy", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Hard", "color": "red"},
                    ]
                }
            },
            "Source": {
                "select": {
                    "options": [
                        {"name": "Lecture", "color": "blue"},
                        {"name": "Textbook", "color": "purple"},
                        {"name": "Lab", "color": "orange"},
                        {"name": "Assignment", "color": "pink"},
                        {"name": "Self-Study", "color": "gray"},
                    ]
                }
            },
            "Word Count": {"number": {}},
            "Created": {"created_time": {}},
        }
    
    @staticmethod
    def study_plans_database_schema() -> Dict[str, Any]:
        """
        Schema for study plans database.
        
        Returns:
            Database properties schema
        """
        return {
            "Title": {"title": {}},
            "Date": {"date": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "yellow"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Completed", "color": "green"},
                    ]
                }
            },
            "Priority Subjects": {"multi_select": {"options": []}},
            "Total Hours": {"number": {}},
            "Completion": {"number": {}},  # Percentage
            "Created": {"created_time": {}},
        }
    
    @staticmethod
    def create_note_page_properties(
        title: str,
        subject: str,
        date: datetime,
        topics: List[str],
        status: str = "Processed",
        difficulty: str = "Medium",
        source: str = "Lecture",
        word_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Create properties for a note page.
        
        Args:
            title: Note title
            subject: Subject name
            date: Note date
            topics: List of topics
            status: Processing status
            difficulty: Difficulty level
            source: Note source
            word_count: Word count
            
        Returns:
            Notion page properties
        """
        return {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Subject": {
                "select": {
                    "name": subject
                }
            },
            "Date": {
                "date": {
                    "start": date.isoformat()
                }
            },
            "Topics": {
                "multi_select": [
                    {"name": topic} for topic in topics
                ]
            },
            "Status": {
                "select": {
                    "name": status
                }
            },
            "Difficulty": {
                "select": {
                    "name": difficulty
                }
            },
            "Source": {
                "select": {
                    "name": source
                }
            },
            "Word Count": {
                "number": word_count
            },
        }
    
    @staticmethod
    def create_study_plan_properties(
        title: str,
        date: datetime,
        priority_subjects: List[str],
        total_hours: float,
        status: str = "Pending",
    ) -> Dict[str, Any]:
        """
        Create properties for a study plan page.
        
        Args:
            title: Plan title
            date: Plan date
            priority_subjects: Priority subjects
            total_hours: Total study hours
            status: Plan status
            
        Returns:
            Notion page properties
        """
        return {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Date": {
                "date": {
                    "start": date.isoformat()
                }
            },
            "Priority Subjects": {
                "multi_select": [
                    {"name": subject} for subject in priority_subjects
                ]
            },
            "Total Hours": {
                "number": total_hours
            },
            "Status": {
                "select": {
                    "name": status
                }
            },
            "Completion": {
                "number": 0
            },
        }
    
    @staticmethod
    def markdown_to_notion_blocks(markdown_text: str) -> List[Dict[str, Any]]:
        """
        Convert markdown text to Notion blocks.
        
        Args:
            markdown_text: Markdown formatted text
            
        Returns:
            List of Notion block objects
        """
        blocks = []
        lines = markdown_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Headings
            if line.startswith('# '):
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith('## '):
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                blocks.append({
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            
            # Bullet list
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            
            # Numbered list
            elif line[0].isdigit() and line[1:3] in ['. ', ') ']:
                blocks.append({
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            
            # Code block
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                blocks.append({
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_lines)}}],
                        "language": "plain text"
                    }
                })
            
            # Quote
            elif line.startswith('> '):
                blocks.append({
                    "type": "quote",
                    "quote": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            
            # Divider
            elif line in ['---', '***', '___']:
                blocks.append({
                    "type": "divider",
                    "divider": {}
                })
            
            # Regular paragraph
            else:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })
            
            i += 1
        
        return blocks
    
    @staticmethod
    def create_summary_callout(summary: str) -> Dict[str, Any]:
        """
        Create a callout block for summary.
        
        Args:
            summary: Summary text
            
        Returns:
            Notion callout block
        """
        return {
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": summary}
                    }
                ],
                "icon": {"emoji": "📝"},
                "color": "blue_background"
            }
        }
    
    @staticmethod
    def create_toggle_block(title: str, content_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a toggle block with nested content.
        
        Args:
            title: Toggle title
            content_blocks: Nested blocks
            
        Returns:
            Notion toggle block
        """
        return {
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": title}}],
                "children": content_blocks
            }
        }