from fastapi import UploadFile
from src.schemas.translate_schema import TranslateResponse
from src.document_handler.document_handler import DocumentHandler
from src.prompt_template import translate_agent


class TranslateService:
    def __init__(self):
        self.agent = translate_agent
        self.doc_handler = DocumentHandler()

    async def translate_text(self, *, text: str, language: str) -> str:
        """Translate text using pydantic-ai agent."""
        result = await self.agent.run(
            f"Target language: {language}\n\nText to translate:\n{text}"
        )
        return result.data.text

    async def translate_file(self, *, file: UploadFile, language: str) -> str:
        """Translate file content."""
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        if not self.doc_handler.is_supported(content_type):
            raise ValueError(f"Unsupported file type: {content_type}")

        text = await self.doc_handler.extract_from_bytes(file_bytes, content_type)

        if not text.strip():
            raise ValueError("Could not extract text from file")

        result = await self.agent.run(
            f"Target language: {language}\n\nText to translate:\n{text}"
        )
        return result.data.text
