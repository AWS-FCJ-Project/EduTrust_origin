from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from src.schemas.translate_schema import TranslateResponse

translate_output_parser = PydanticOutputParser(pydantic_object=TranslateResponse)

translate_prompt_template = PromptTemplate(
    template=(
        "You are a translation engine.\n"
        "Translate accurately into the target language.\n"
        "Preserve meaning, tone, and formatting.\n"
        "Return documentation strictly following the format instructions.\n\n"
        "Target language:\n{language}\n\n"
        "Text to translate:\n{text}\n\n"
        "{format_instructions}"
    ),
    input_variables=["language", "text"],
    partial_variables={
        "format_instructions": translate_output_parser.get_format_instructions()
    },
)
