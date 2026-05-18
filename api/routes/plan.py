import logging
from fastapi import APIRouter, Depends, HTTPException, status
from api.middleware.auth import verify_api_key
from api.models.requests import PlanRequest, PlanResponse, TaskResult as ApiTaskResult
from models import TaskPlanInput, ExecutionMode
from skills.research import ResearchSkill
from skills.task_planner import TaskPlannerSkill

logger = logging.getLogger("api")
router = APIRouter()

# Single skill instances shared across all requests
_research_skill = ResearchSkill()
task_planner = TaskPlannerSkill(research_skill=_research_skill)


@router.post("/plan", response_model=PlanResponse, dependencies=[Depends(verify_api_key)])
async def plan(request: PlanRequest):
    """
    Calls the Task Planning Skill directly.

    Steps:
    1. Convert the API request into a TaskPlanInput
    2. Run the task planner skill
    3. Convert the output into a PlanResponse and return it
    """
    try:
        logger.info(f"Running task planner for goal: {request.goal}")

        # Step 1: Build skill input from API request
        plan_input = TaskPlanInput(
            goal=request.goal,
            context=request.context,
            constraints=request.constraints,
            execution_mode=ExecutionMode.PLAN_ONLY
        )

        # Step 2: Run the task planner
        output = task_planner.run(plan_input)

        # Step 3: Convert skill output to API response format
        return PlanResponse(
            plan=[
                ApiTaskResult(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    depends_on=t.depends_on,
                    estimated_duration=t.estimated_duration
                )
                for t in output.plan
            ],
            next_action=output.next_action,
            blockers=output.blockers
        )

    except Exception as e:
        logger.error(f"Error in /plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the plan: {str(e)}"
        )
