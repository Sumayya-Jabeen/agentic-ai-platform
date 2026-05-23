from pydantic import BaseModel, Field
from typing import List, Optional


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    What the frontend sends when the user types a message.

    - message: the user's text
    - session_id: optional. If provided, the backend loads previous
                  conversation turns so the AI remembers context.
                  If omitted, a new session is created automatically.
    """
    message: str = Field(description="The user's message or goal")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to continue an existing conversation"
    )


class ChatResponse(BaseModel):
    """
    What the backend returns after the AI responds.

    - reply: the AI's answer
    - session_id: the session ID to pass back in the next request
    """
    reply: str
    session_id: str


# ─── Research ─────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    """
    What the frontend sends to trigger the Research Skill directly.
    """
    query: str = Field(description="The topic or question to research")
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Optional sub-topics to focus on during research"
    )


class SourceResult(BaseModel):
    """A single source returned by the research skill."""
    title: str
    url: str
    credibility_score: float


class ResearchResponse(BaseModel):
    """
    Structured research result returned to the frontend.
    """
    summary: str
    key_points: List[str]
    sources: List[SourceResult]
    gaps: List[str]
    confidence: float


# ─── Plan ─────────────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    """
    What the frontend sends to trigger the Task Planner Skill directly.
    """
    goal: str = Field(description="The high-level goal to plan for")
    context: Optional[str] = Field(
        default=None,
        description="Optional research summary to inform the plan"
    )
    constraints: Optional[List[str]] = Field(
        default=None,
        description="Optional limits like time, budget, or resource restrictions"
    )


class TaskResult(BaseModel):
    """A single task in the plan returned to the frontend."""
    id: str
    title: str
    description: str
    depends_on: List[str]
    estimated_duration: Optional[str]


class PlanResponse(BaseModel):
    """
    Structured task plan returned to the frontend.
    """
    plan: List[TaskResult]
    next_action: Optional[str]
    blockers: List[str]
