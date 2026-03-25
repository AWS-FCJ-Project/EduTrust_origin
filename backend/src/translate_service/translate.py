from typing import Any

import yaml
from fastapi import UploadFile
from pydantic_ai import Agent
from src.app_config import app_config
from src.document_handler.document_handler import DocumentHandler
from src.llm import LLM
from src.prompt_template import TRANSLATE_INSTRUCTIONS
from src.schemas.translate_schema import TranslateResponse


class TranslateService:
    def __init__(self) -> None:
        self._llms_config = self._load_config()
        self._model_name = app_config.TRANSLATE_MODEL or self._llms_config.get(
            "translate_model"
        )
        self._agent = self._create_agent()
        self.doc_handler = DocumentHandler()

    def _load_config(self) -> dict[str, Any]:
        with open(app_config.LLMS_CONFIG_PATH) as file:
            return yaml.safe_load(file) or {}

    def _create_agent(self) -> Agent[None, TranslateResponse]:
        model = LLM().init_chat_model(self._model_name)
        return Agent(
            model, instructions=TRANSLATE_INSTRUCTIONS, output_type=TranslateResponse
        )

    def _build_prompt(self, *, text: str, language: str) -> str:
        """Build prompt for translation."""
        return f"{TRANSLATE_INSTRUCTIONS}\n\nTarget language: {language}\n\nText to translate:\n{text}"

    async def translate_text(self, *, text: str, language: str) -> str:
        """Translate text."""
        prompt = self._build_prompt(text=text, language=language)
        result = await self._agent.run(prompt)
        return result.output.text

    async def translate_file(self, *, file: UploadFile, language: str) -> str:
        """Translate file content."""
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        if not self.doc_handler.is_supported(content_type):
            raise ValueError(f"Unsupported file type: {content_type}")

        text = await self.doc_handler.extract_from_bytes(file_bytes, content_type)

        if not text.strip():
            raise ValueError("Could not extract text from file")

        return await self.translate_text(text=text, language=language)
