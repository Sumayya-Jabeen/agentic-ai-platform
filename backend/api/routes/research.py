import logging
from fastapi import APIRouter, Depends, HTTPException, status
from api.middleware.auth import verify_api_key
from api.models.requests import ResearchRequest, ResearchResponse, SourceResult
from models import ResearchInput
from skills.research import ResearchSkill

logger = logging.getLogger("api")
router = APIRouter()

# Single research skill instance shared across all requests
research_skill = ResearchSkill()


@router.post("/research", response_model=ResearchResponse, dependencies=[Depends(verify_api_key)])
async def research(request: ResearchRequest):
    """
    Calls the Research & Summarization Skill directly.

    Steps:
    1. Convert the API request into a ResearchInput
    2. Run the research skill
    3. Convert the output into a ResearchResponse and return it
    """
    try:
        logger.info(f"Running research skill for query: {request.query}")

        # Step 1: Build skill input from API request
        research_input = ResearchInput(
            query=request.query,
            focus_areas=request.focus_areas
        )

        # Step 2: Run the research skill
        output = research_skill.run(research_input)

        # Step 3: Convert skill output to API response format
        return ResearchResponse(
            summary=output.summary,
            key_points=output.key_points,
            sources=[
                SourceResult(
                    title=s.title,
                    url=s.url,
                    credibility_score=s.credibility_score
                )
                for s in output.sources
            ],
            gaps=output.gaps,
            confidence=output.confidence
        )

    except Exception as e:
        logger.error(f"Error in /research: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while running research: {str(e)}"
        )
