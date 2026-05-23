from typing import Any, Dict
from models import Task, TaskStatus


class TaskExecutor:
    """
    Executes individual tasks from a plan.

    Think of this as the "worker" — the Task Planner creates the to-do list,
    and the TaskExecutor is the one who actually does each item on that list.
    """

    def __init__(self, research_skill=None):
        # research_skill is optional — injected so the executor can
        # call it when a task requires information gathering
        self.research_skill = research_skill

    def execute(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task and return the result.

        Steps:
        1. Mark the task as in-progress
        2. Run the right action based on what tool the task needs
        3. Mark it completed or failed
        4. Return a result dict
        """
        task.status = TaskStatus.IN_PROGRESS

        try:
            if task.tool_required == "research_skill" and self.research_skill:
                result = self._run_research_task(task)
            else:
                result = self._run_generic_task(task)

            task.status = TaskStatus.COMPLETED
            return {"task_id": task.id, "status": "completed", "result": result}

        except Exception as e:
            task.status = TaskStatus.FAILED
            return {"task_id": task.id, "status": "failed", "error": str(e)}

    def _run_research_task(self, task: Task) -> str:
        """
        Run a task that requires research.

        Uses the task description as the research query and returns
        the summary from the Research Skill.
        """
        from models import ResearchInput
        research_input = ResearchInput(query=task.description)
        output = self.research_skill.run(research_input)
        return output.summary

    def _run_generic_task(self, task: Task) -> str:
        """
        Handle tasks that don't need a specific tool.

        These are tasks a human would complete manually —
        the executor acknowledges them and flags them for the user.
        """
        return f"Task '{task.title}' has been noted. Manual execution required."
