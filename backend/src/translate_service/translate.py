from fastapi import UploadFile
from langchain_litellm import ChatLiteLLM

from src.app_config import app_config
from src.document_handler.document_handler import DocumentHandler
from src.prompt_template import translate_output_parser, translate_prompt_template


class TranslateService:
    def __init__(self):
        self.model = app_config.TRANSLATE_MODEL
        self.llm = ChatLiteLLM(model=self.model, temperature=0)
        self.chain = translate_prompt_template | self.llm | translate_output_parser
        self.doc_handler = DocumentHandler()

    async def translate_text(self, *, text: str, language: str) -> str:
        """Translate text."""
        result = await self.chain.ainvoke({"language": language, "text": text})
        return result.text

    async def translate_file(self, *, file: UploadFile, language: str) -> str:
        """Translate file content."""
        file_bytes = await file.read()
        content_type = file.content_type or "application/octet-stream"

        if not self.doc_handler.is_supported(content_type):
            raise ValueError(f"Unsupported file type: {content_type}")

        text = await self.doc_handler.extract_from_bytes(file_bytes, content_type)

        if not text.strip():
            raise ValueError("Could not extract text from file")

        result = await self.chain.ainvoke({"language": language, "text": text})
        return result.text
