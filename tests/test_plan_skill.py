"""
Unit tests for the Task Planning & Execution Skill.

LLM calls are mocked so no real API calls are made.
Tests verify output schema, task structure, dependencies, and error handling.
"""

import pytest
from unittest.mock import patch
from models import (
    TaskPlanInput, TaskPlanOutput, Task, TaskStatus,
    StatusSummary, ExecutionMode
)
from skills.task_planner import TaskPlannerSkill


# ── Shared mock output ────────────────────────────────────────────────────────

MOCK_PLAN_OUTPUT = TaskPlanOutput(
    plan=[
        Task(
            id="task_1",
            title="Define project requirements",
            description="Document all functional and non-functional requirements",
            depends_on=[],
            estimated_duration="2 days",
            status=TaskStatus.PENDING,
        ),
        Task(
            id="task_2",
            title="Design system architecture",
            description="Create high-level architecture diagram and component breakdown",
            depends_on=["task_1"],
            estimated_duration="3 days",
            status=TaskStatus.PENDING,
        ),
        Task(
            id="task_3",
            title="Implement backend API",
            description="Build FastAPI backend with all required endpoints",
            depends_on=["task_2"],
            estimated_duration="1 week",
            status=TaskStatus.PENDING,
        ),
        Task(
            id="task_4",
            title="Build frontend interface",
            description="Create Next.js frontend with all UI components",
            depends_on=["task_2"],
            estimated_duration="1 week",
            status=TaskStatus.PENDING,
        ),
    ],
    status_summary=StatusSummary(total=4, completed=0, failed=0, pending=4),
    next_action="Start with task_1 — requirements must be defined first",
    blockers=[],
)


@pytest.fixture
def skill():
    return TaskPlannerSkill()


# ── Output schema ─────────────────────────────────────────────────────────────

def test_plan_output_is_correct_type(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    assert isinstance(result, TaskPlanOutput)


# ── Tasks ─────────────────────────────────────────────────────────────────────

def test_plan_returns_tasks(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    assert isinstance(result.plan, list)
    assert len(result.plan) > 0


def test_plan_tasks_have_unique_ids(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    ids = [t.id for t in result.plan]
    assert len(ids) == len(set(ids)), "Task IDs must be unique"


def test_plan_tasks_have_required_fields(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    for task in result.plan:
        assert isinstance(task.id, str) and len(task.id) > 0
        assert isinstance(task.title, str) and len(task.title) > 0
        assert isinstance(task.description, str) and len(task.description) > 0


def test_plan_tasks_have_status(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    for task in result.plan:
        assert isinstance(task.status, TaskStatus)


def test_plan_tasks_have_duration_estimates(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    for task in result.plan:
        assert task.estimated_duration is not None
        assert len(task.estimated_duration) > 0


# ── Dependencies ──────────────────────────────────────────────────────────────

def test_plan_dependencies_reference_valid_task_ids(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    valid_ids = {t.id for t in result.plan}
    for task in result.plan:
        for dep in task.depends_on:
            assert dep in valid_ids, f"Task '{task.id}' depends on unknown '{dep}'"


def test_plan_first_task_has_no_dependencies(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    assert result.plan[0].depends_on == []


# ── Status summary ────────────────────────────────────────────────────────────

def test_plan_has_status_summary(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    assert isinstance(result.status_summary, StatusSummary)


def test_plan_status_summary_total_matches_plan_length(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(goal="Build a web application"))
    assert result.status_summary.total == len(result.plan)


# ── Input options ─────────────────────────────────────────────────────────────

def test_plan_accepts_constraints(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(
            goal="Build a web application",
            constraints=["Complete in 2 weeks", "Budget under $5000"]
        ))
    assert isinstance(result, TaskPlanOutput)


def test_plan_accepts_research_context(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(
            goal="Build a web application",
            context="Research shows Next.js is the best frontend framework..."
        ))
    assert isinstance(result, TaskPlanOutput)


def test_plan_accepts_max_tasks_limit(skill):
    with patch.object(skill, "_generate_plan", return_value=MOCK_PLAN_OUTPUT):
        result = skill.run(TaskPlanInput(
            goal="Build a web application",
            max_tasks=5
        ))
    assert len(result.plan) <= 5


# ── Error handling ────────────────────────────────────────────────────────────

def test_plan_propagates_llm_error(skill):
    with patch.object(skill, "_generate_plan", side_effect=RuntimeError("LLM timeout")):
        with pytest.raises(RuntimeError, match="LLM timeout"):
            skill.run(TaskPlanInput(goal="Build a web application"))
