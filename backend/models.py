from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ─── Shared enums ────────────────────────────────────────────────────────────

class OutputFormat(str, Enum):
    BULLET_POINTS = "bullet_points"
    PARAGRAPH = "paragraph"
    STRUCTURED = "structured"


class ExecutionMode(str, Enum):
    PLAN_ONLY = "plan_only"
    PLAN_AND_EXECUTE = "plan_and_execute"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ─── Research & Summarization Skill ──────────────────────────────────────────

class ResearchInput(BaseModel):
    """
    Given a topic or question, this skill searches the web for relevant sources,
    extracts and filters the most useful content, and returns a structured summary
    with key points, sources, and confidence level — ready to be consumed by other
    skills or presented directly to the user.

    Research depth is fixed at shallow (3-5 sources) for fast, focused results.
    """

    query: str = Field(description="The topic or question to research")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Narrow the research to specific sub-topics"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.STRUCTURED,
        description=(
            "Format of the returned summary: 'bullet_points' for a quick scannable list, "
            "'paragraph' for a readable narrative, or 'structured' for a full JSON object "
            "with summary, key points, sources, and confidence score."
        )
    )


class Source(BaseModel):
    """A single research source returned by the web search."""

    url: str
    title: str
    snippet: Optional[str] = Field(
        default=None,
        description="Short text excerpt from the source — stored directly from Tavily to avoid re-fetching the full page"
    )
    credibility_score: float = Field(default=0.7, ge=0.0, le=1.0)


class ResearchOutput(BaseModel):
    """Output contract for the Research & Summarization Skill."""

    summary: str
    key_points: List[str]
    sources: List[Source]
    gaps: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


# ─── Task Planning & Execution Skill ─────────────────────────────────────────

class Task(BaseModel):
    """A single atomic task in the plan."""

    id: str
    title: str
    description: str
    depends_on: List[str] = Field(default_factory=list)
    tool_required: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    estimated_duration: Optional[str] = None


class TaskPlanInput(BaseModel):
    """Input contract for the Task Planning & Execution Skill."""

    goal: str = Field(description="The high-level objective to accomplish")
    context: Optional[str] = Field(
        default=None,
        description="Research output or background info to inform the plan"
    )
    constraints: Optional[List[str]] = Field(
        default=None,
        description="Limits: time, resources, forbidden actions"
    )
    execution_mode: ExecutionMode = Field(default=ExecutionMode.PLAN_ONLY)
    max_tasks: Optional[int] = Field(default=10)


class StatusSummary(BaseModel):
    total: int
    completed: int
    failed: int
    pending: int


class TaskResult(BaseModel):
    """Result of executing a single task."""

    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


class TaskPlanOutput(BaseModel):
    """Output contract for the Task Planning & Execution Skill."""

    plan: List[Task]
    execution_results: List[TaskResult] = Field(default_factory=list)
    status_summary: StatusSummary
    next_action: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)
