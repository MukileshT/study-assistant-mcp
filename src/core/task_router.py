"""
Task routing and prioritization logic.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskType(Enum):
    """Types of tasks the agent can perform."""
    PROCESS_NOTE = "process_note"
    GENERATE_PLAN = "generate_plan"
    ANALYZE_CONTENT = "analyze_content"
    FORMAT_TEXT = "format_text"
    BATCH_PROCESS = "batch_process"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """Represents a task to be executed."""
    
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    data: Dict[str, Any]
    created_at: datetime
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __lt__(self, other):
        """Compare tasks by priority for queue sorting."""
        return self.priority.value > other.priority.value  # Higher priority first


class TaskRouter:
    """Routes tasks to appropriate handlers."""
    
    def __init__(self):
        """Initialize task router."""
        self.task_handlers = {
            TaskType.PROCESS_NOTE: self._handle_process_note,
            TaskType.GENERATE_PLAN: self._handle_generate_plan,
            TaskType.ANALYZE_CONTENT: self._handle_analyze_content,
            TaskType.FORMAT_TEXT: self._handle_format_text,
            TaskType.BATCH_PROCESS: self._handle_batch_process,
        }
        
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        logger.info("Task router initialized")
    
    def create_task(
        self,
        task_type: TaskType,
        data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """
        Create a new task.
        
        Args:
            task_type: Type of task
            data: Task data
            priority: Task priority
            
        Returns:
            Created task
        """
        task_id = self._generate_task_id()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            data=data,
            created_at=datetime.now(),
        )
        
        self.active_tasks[task_id] = task
        
        logger.info(
            f"Created task: {task_id} ({task_type.value}, priority={priority.value})"
        )
        
        return task
    
    async def route_task(self, task: Task) -> Task:
        """
        Route task to appropriate handler.
        
        Args:
            task: Task to route
            
        Returns:
            Updated task with result or error
        """
        logger.info(f"Routing task: {task.task_id} ({task.task_type.value})")
        
        task.status = "processing"
        
        try:
            handler = self.task_handlers.get(task.task_type)
            
            if handler is None:
                raise ValueError(f"No handler for task type: {task.task_type}")
            
            result = await handler(task.data)
            
            task.status = "completed"
            task.result = result
            
            logger.info(f"Task completed: {task.task_id}")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            
            logger.error(f"Task failed: {task.task_id} - {str(e)}")
        
        # Move to completed
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        self.completed_tasks.append(task)
        
        return task
    
    async def _handle_process_note(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle note processing task."""
        # This will be called by the agent
        return {"status": "delegated_to_agent"}
    
    async def _handle_generate_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle plan generation task."""
        return {"status": "delegated_to_planner"}
    
    async def _handle_analyze_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle content analysis task."""
        return {"status": "delegated_to_analyzer"}
    
    async def _handle_format_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text formatting task."""
        return {"status": "delegated_to_formatter"}
    
    async def _handle_batch_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch processing task."""
        return {"status": "delegated_to_batch_processor"}
    
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Prioritize tasks based on priority and type.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Sorted list of tasks
        """
        return sorted(tasks, key=lambda t: (
            -t.priority.value,  # Higher priority first
            t.created_at  # Earlier first
        ))
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Check completed tasks
        for task in self.completed_tasks:
            if task.task_id == task_id:
                return task
        
        return None
    
    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks."""
        return list(self.active_tasks.values())
    
    def get_completed_tasks(self, limit: int = 100) -> List[Task]:
        """Get completed tasks."""
        return self.completed_tasks[-limit:]
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics."""
        total_completed = len(self.completed_tasks)
        
        successful = sum(1 for t in self.completed_tasks if t.status == "completed")
        failed = sum(1 for t in self.completed_tasks if t.status == "failed")
        
        # Task types breakdown
        type_counts = {}
        for task in self.completed_tasks:
            task_type = task.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        return {
            "active_tasks": len(self.active_tasks),
            "total_completed": total_completed,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / max(total_completed, 1),
            "task_types": type_counts,
        }
    
    def clear_completed(self, keep_recent: int = 50):
        """
        Clear old completed tasks.
        
        Args:
            keep_recent: Number of recent tasks to keep
        """
        if len(self.completed_tasks) > keep_recent:
            self.completed_tasks = self.completed_tasks[-keep_recent:]
            logger.info(f"Cleared old tasks, keeping {keep_recent} recent")
    
    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        import uuid
        return f"task_{uuid.uuid4().hex[:8]}"
    
    def determine_priority(
        self,
        task_type: TaskType,
        data: Dict[str, Any]
    ) -> TaskPriority:
        """
        Automatically determine task priority.
        
        Args:
            task_type: Type of task
            data: Task data
            
        Returns:
            Determined priority
        """
        # Plan generation is usually high priority
        if task_type == TaskType.GENERATE_PLAN:
            return TaskPriority.HIGH
        
        # Batch processing is lower priority
        if task_type == TaskType.BATCH_PROCESS:
            return TaskPriority.LOW
        
        # Check for urgency flags in data
        if data.get("urgent", False):
            return TaskPriority.URGENT
        
        # Default to medium
        return TaskPriority.MEDIUM