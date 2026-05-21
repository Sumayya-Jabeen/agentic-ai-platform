import logging
from langchain_openai import ChatOpenAI
from models import TaskPlanInput, TaskPlanOutput, TaskStatus, StatusSummary, TaskResult
from tools.executor import TaskExecutor
from callbacks import PipelineLogger
from config import config


logger = logging.getLogger("api")

SYSTEM_PROMPT = """You are a task planning expert. Given a high-level goal, break it down
into a concrete, ordered list of actionable tasks.

For each task follow these rules:
- Give it a unique id like 'task_1', 'task_2', and so on
- Make the title short and the description specific and actionable
- List dependencies — which task ids must finish before this one can start
- Set tool_required to 'research_skill' if the task needs information gathering, otherwise leave it null
- Provide a realistic estimated_duration like '30 minutes' or '1 week'

Keep the plan focused and practical. Do not over-engineer."""


class TaskPlannerSkill:
    """
    Task Planning & Execution Skill.

    How it works:
    - Step 1 (Plan): with_structured_output() sends the goal to the model and
                     returns a validated TaskPlanOutput directly.
    - Step 2 (Execute): If execution_mode is 'plan_and_execute', the executor
                        runs each task in dependency order.
    """

    def __init__(self, research_skill=None):
        self.llm = ChatOpenAI(
            model=config.model,
            api_key=config.openai_api_key,
            max_completion_tokens=config.max_completion_tokens
        )
        self.executor = TaskExecutor(research_skill=research_skill)

    def run(self, input: TaskPlanInput) -> TaskPlanOutput:
        """Main entry point. Takes a TaskPlanInput and returns a TaskPlanOutput."""
        logger.info(f"  [PLANNER] Starting task planning for goal: '{input.goal}'")
        logger.info(f"  [PLANNER] Execution mode: {input.execution_mode.value}")
        if input.context:
            logger.info(f"  [PLANNER] Research context provided: {len(input.context)} chars")

        try:
            # Step 1: Generate the plan
            output = self._generate_plan(input)

            # Step 2: Execute if requested
            if input.execution_mode.value == "plan_and_execute":
                output = self._execute_plan(output)

            return output

        except Exception as e:
            logger.error(
                f"  [PLANNER] ERROR during planning for '{input.goal}': "
                f"{type(e).__name__}: {e}"
            )
            raise

    # ─── Step 1: Plan Generation ──────────────────────────────────────────────

    def _generate_plan(self, input: TaskPlanInput) -> TaskPlanOutput:
        """
        with_structured_output() replaces client.beta.chat.completions.parse().
        Returns a fully validated TaskPlanOutput Pydantic model directly.
        """
        logger.info(f"  [PLANNER] Step 1 START — generating structured task plan")

        cb = PipelineLogger("PLANNER-GEN")
        structured_llm = self.llm.with_structured_output(TaskPlanOutput)

        context_section = (
            f"\n\nContext / Research:\n{input.context}"
            if input.context else ""
        )
        constraints_section = (
            f"\n\nConstraints:\n" + "\n".join(f"- {c}" for c in input.constraints)
            if input.constraints else ""
        )
        max_tasks_note = (
            f"\n\nKeep the plan to a maximum of {input.max_tasks} tasks."
            if input.max_tasks else ""
        )

        output: TaskPlanOutput = structured_llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    f"Create a task plan for this goal: {input.goal}"
                    f"{context_section}"
                    f"{constraints_section}"
                    f"{max_tasks_note}"
                )
            ],
            config={"callbacks": [cb]}
        )

        task_ids = [t.id for t in output.plan]
        logger.info(
            f"  [PLANNER] Step 1 COMPLETE | "
            f"tasks generated: {len(output.plan)} | "
            f"task IDs: {task_ids} | "
            f"next_action: '{output.next_action}' | "
            f"{cb.summary()}"
        )
        return output

    # ─── Step 2: Plan Execution ───────────────────────────────────────────────

    def _execute_plan(self, output: TaskPlanOutput) -> TaskPlanOutput:
        """
        Execute each task in the plan in dependency order.

        A task is skipped if any of its dependencies have not completed.
        Results are stored as TaskResult objects in output.execution_results.
        """
        logger.info(
            f"  [PLANNER] Step 2 START — executing {len(output.plan)} tasks"
        )

        completed_ids = set()

        for i, task in enumerate(output.plan, start=1):
            unmet = [dep for dep in task.depends_on if dep not in completed_ids]
            if unmet:
                task.status = TaskStatus.SKIPPED
                output.blockers.append(
                    f"Task '{task.id}' skipped — waiting on: {', '.join(unmet)}"
                )
                logger.warning(
                    f"  [PLANNER] Task {i}/{len(output.plan)} '{task.id}' SKIPPED — "
                    f"unmet dependencies: {unmet}"
                )
                continue

            logger.info(
                f"  [PLANNER] Task {i}/{len(output.plan)} '{task.id}': "
                f"'{task.title}' — executing"
            )
            result = self.executor.execute(task)
            output.execution_results.append(TaskResult(**result))

            if result["status"] == "completed":
                completed_ids.add(task.id)
                logger.info(
                    f"  [PLANNER] Task '{task.id}' COMPLETED"
                )
            else:
                logger.warning(
                    f"  [PLANNER] Task '{task.id}' status: {result['status']}"
                )

        statuses = [t.status for t in output.plan]
        output.status_summary = StatusSummary(
            total=len(output.plan),
            completed=statuses.count(TaskStatus.COMPLETED),
            failed=statuses.count(TaskStatus.FAILED),
            pending=statuses.count(TaskStatus.PENDING)
        )

        logger.info(
            f"  [PLANNER] Step 2 COMPLETE | "
            f"total: {output.status_summary.total} | "
            f"completed: {output.status_summary.completed} | "
            f"failed: {output.status_summary.failed} | "
            f"pending: {output.status_summary.pending}"
        )
        return output
