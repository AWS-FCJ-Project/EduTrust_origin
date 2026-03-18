from fastapi import APIRouter
from src.crew.agents import quiz_agent
from src.schemas.practice_schema import GenerateQuestionsRequest, GenerateQuestionsResponse

router = APIRouter(prefix="/practice", tags=["Practice"])


@router.post("/generate", response_model=GenerateQuestionsResponse)
async def generate_questions(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    """
    Generate quiz questions using the quiz_agent directly.
    The prompt describes the topic/type of questions, and num_questions sets the count.
    """
    instruction = (
        f"Generate exactly {request.num_questions} quiz questions based on the following description:\n"
        f"{request.prompt}\n\n"
        "Format your response as a numbered list. For multiple-choice questions, include 4 options (A, B, C, D) "
        "and clearly mark the correct answer. For essay questions, include a suggested answer guide. "
        "Respond in the same language as the description."
    )
    result = await quiz_agent.run(instruction)
    return GenerateQuestionsResponse(raw=result.output)
