"""
Workflow engine for managing multi-stage processing pipelines.
"""

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.logger import get_logger
from src.utils.error_handlers import handle_error

logger = get_logger(__name__)


class StageStatus(Enum):
    """Status of a workflow stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStage:
    """Represents a stage in a workflow."""
    
    name: str
    handler: Callable
    description: str = ""
    required: bool = True
    retry_count: int = 0
    max_retries: int = 2
    status: StageStatus = StageStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get stage duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class Workflow:
    """Represents a complete workflow."""
    
    workflow_id: str
    name: str
    stages: List[WorkflowStage]
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_stage_index: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Get total workflow duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def progress(self) -> float:
        """Get workflow progress as percentage."""
        if not self.stages:
            return 0.0
        
        completed = sum(
            1 for stage in self.stages
            if stage.status in [StageStatus.COMPLETED, StageStatus.SKIPPED]
        )
        return (completed / len(self.stages)) * 100


class WorkflowEngine:
    """Engine for executing multi-stage workflows."""
    
    def __init__(self):
        """Initialize workflow engine."""
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_templates: Dict[str, List[WorkflowStage]] = {}
        
        # Register default workflows
        self._register_default_workflows()
        
        logger.info("Workflow engine initialized")
    
    def _register_default_workflows(self):
        """Register default workflow templates."""
        
        # Note processing workflow
        self.register_workflow_template(
            "process_note",
            [
                WorkflowStage(
                    name="preprocessing",
                    handler=None,  # Will be set when workflow is created
                    description="Preprocess and enhance image",
                    required=False,
                ),
                WorkflowStage(
                    name="ocr_extraction",
                    handler=None,
                    description="Extract text from image",
                    required=True,
                ),
                WorkflowStage(
                    name="content_analysis",
                    handler=None,
                    description="Analyze content and extract metadata",
                    required=True,
                ),
                WorkflowStage(
                    name="text_formatting",
                    handler=None,
                    description="Format text as markdown",
                    required=True,
                ),
                WorkflowStage(
                    name="notion_upload",
                    handler=None,
                    description="Upload to Notion",
                    required=True,
                ),
                WorkflowStage(
                    name="database_save",
                    handler=None,
                    description="Save to local database",
                    required=True,
                ),
            ]
        )
        
        # Plan generation workflow
        self.register_workflow_template(
            "generate_plan",
            [
                WorkflowStage(
                    name="gather_recent_notes",
                    handler=None,
                    description="Gather recent note data",
                    required=True,
                ),
                WorkflowStage(
                    name="analyze_learning_patterns",
                    handler=None,
                    description="Analyze learning patterns",
                    required=True,
                ),
                WorkflowStage(
                    name="generate_plan",
                    handler=None,
                    description="Generate study plan",
                    required=True,
                ),
                WorkflowStage(
                    name="upload_plan",
                    handler=None,
                    description="Upload plan to Notion",
                    required=True,
                ),
            ]
        )
    
    def register_workflow_template(
        self,
        template_name: str,
        stages: List[WorkflowStage]
    ):
        """
        Register a workflow template.
        
        Args:
            template_name: Name of template
            stages: List of workflow stages
        """
        self.workflow_templates[template_name] = stages
        logger.info(f"Registered workflow template: {template_name}")
    
    def create_workflow(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create a workflow from template.
        
        Args:
            template_name: Name of template
            context: Initial workflow context
            
        Returns:
            Created workflow
        """
        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")
        
        # Copy stages from template
        stages = [
            WorkflowStage(
                name=stage.name,
                handler=stage.handler,
                description=stage.description,
                required=stage.required,
                max_retries=stage.max_retries,
            )
            for stage in self.workflow_templates[template_name]
        ]
        
        workflow_id = self._generate_workflow_id()
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=template_name,
            stages=stages,
            context=context or {},
        )
        
        self.workflows[workflow_id] = workflow
        
        logger.info(f"Created workflow: {workflow_id} ({template_name})")
        
        return workflow
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        handlers: Optional[Dict[str, Callable]] = None,
    ) -> Workflow:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            handlers: Stage handlers (if not set in stages)
            
        Returns:
            Completed workflow
        """
        logger.info(f"Starting workflow execution: {workflow.workflow_id}")
        
        workflow.status = "running"
        workflow.started_at = datetime.now()
        
        try:
            for i, stage in enumerate(workflow.stages):
                workflow.current_stage_index = i
                
                # Get handler
                handler = stage.handler or (handlers or {}).get(stage.name)
                
                if handler is None:
                    logger.warning(f"No handler for stage: {stage.name}")
                    stage.status = StageStatus.SKIPPED
                    continue
                
                # Execute stage
                success = await self._execute_stage(stage, handler, workflow.context)
                
                # Check if required stage failed
                if not success and stage.required:
                    logger.error(f"Required stage failed: {stage.name}")
                    workflow.status = "failed"
                    break
            
            # Check overall status
            if workflow.status != "failed":
                failed_required = any(
                    s.status == StageStatus.FAILED and s.required
                    for s in workflow.stages
                )
                
                if failed_required:
                    workflow.status = "failed"
                else:
                    workflow.status = "completed"
            
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            workflow.status = "failed"
            handle_error(e, {"workflow_id": workflow.workflow_id})
        
        workflow.completed_at = datetime.now()
        
        logger.info(
            f"Workflow {workflow.status}: {workflow.workflow_id} "
            f"(duration: {workflow.duration:.2f}s)"
        )
        
        return workflow
    
    async def _execute_stage(
        self,
        stage: WorkflowStage,
        handler: Callable,
        context: Dict[str, Any],
    ) -> bool:
        """
        Execute a single workflow stage.
        
        Args:
            stage: Stage to execute
            handler: Stage handler function
            context: Workflow context
            
        Returns:
            True if successful
        """
        logger.info(f"Executing stage: {stage.name}")
        
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now()
        
        while stage.retry_count <= stage.max_retries:
            try:
                # Execute handler
                result = await handler(context)
                
                # Update stage
                stage.status = StageStatus.COMPLETED
                stage.result = result
                stage.completed_at = datetime.now()
                
                # Update context with result
                context[f"{stage.name}_result"] = result
                
                logger.info(
                    f"Stage completed: {stage.name} "
                    f"(duration: {stage.duration:.2f}s)"
                )
                
                return True
                
            except Exception as e:
                stage.retry_count += 1
                
                if stage.retry_count > stage.max_retries:
                    logger.error(
                        f"Stage failed after {stage.max_retries} retries: "
                        f"{stage.name} - {str(e)}"
                    )
                    stage.status = StageStatus.FAILED
                    stage.error = str(e)
                    stage.completed_at = datetime.now()
                    return False
                else:
                    logger.warning(
                        f"Stage failed, retrying ({stage.retry_count}/"
                        f"{stage.max_retries}): {stage.name}"
                    )
        
        return False
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Status dictionary
        """
        workflow = self.get_workflow(workflow_id)
        
        if workflow is None:
            return {"error": "Workflow not found"}
        
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "progress": workflow.progress,
            "current_stage": workflow.stages[workflow.current_stage_index].name
            if workflow.current_stage_index < len(workflow.stages)
            else None,
            "stages": [
                {
                    "name": stage.name,
                    "status": stage.status.value,
                    "duration": stage.duration,
                }
                for stage in workflow.stages
            ],
            "duration": workflow.duration,
        }
    
    def list_workflows(self, status: Optional[str] = None) -> List[Workflow]:
        """
        List workflows, optionally filtered by status.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of workflows
        """
        workflows = list(self.workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        return workflows
    
    def cleanup_completed(self, keep_recent: int = 50):
        """
        Clean up old completed workflows.
        
        Args:
            keep_recent: Number of recent workflows to keep
        """
        completed = [
            w for w in self.workflows.values()
            if w.status in ["completed", "failed"]
        ]
        
        if len(completed) > keep_recent:
            # Sort by completion time
            completed.sort(key=lambda w: w.completed_at or datetime.min)
            
            # Remove old ones
            to_remove = completed[:-keep_recent]
            for workflow in to_remove:
                del self.workflows[workflow.workflow_id]
            
            logger.info(f"Cleaned up {len(to_remove)} old workflows")
    
    def _generate_workflow_id(self) -> str:
        """Generate unique workflow ID."""
        import uuid
        return f"wf_{uuid.uuid4().hex[:8]}"