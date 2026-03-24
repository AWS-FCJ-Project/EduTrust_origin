from pydantic_ai import Agent
from src.llm import LLM
from src.schemas.translate_schema import TranslateResponse

# Initialize the LLM wrapper
llm_manager = LLM()

# Create a pydantic-ai Agent for translation
translate_agent = Agent(
    model=llm_manager.chat_model("TRANSLATE_MODEL"),
    result_type=TranslateResponse,
    system_prompt=(
        "You are a translation engine.\n"
        "Translate accurately into the target language.\n"
        "Preserve meaning, tone, and formatting.\n"
        "Return documentation strictly following the format instructions."
    )
)
