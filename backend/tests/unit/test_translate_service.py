from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.translate_service.translate import TranslateService


@pytest.fixture
def translate_service() -> TranslateService:
    translate_service_instance = object.__new__(TranslateService)
    translate_service_instance._agent = MagicMock()
    translate_service_instance.doc_handler = MagicMock()
    return translate_service_instance


def make_upload_file(*, content_type: str, file_bytes: bytes) -> Any:
    upload_file = SimpleNamespace(
        content_type=content_type, read=AsyncMock(return_value=file_bytes)
    )
    return upload_file


class TestTranslateService:
    @pytest.mark.asyncio
    async def test_translate_text(self, translate_service: TranslateService) -> None:
        mock_result = MagicMock()
        mock_result.output.text = "xin chao"
        translate_service._agent.run = AsyncMock(return_value=mock_result)

        result = await translate_service.translate_text(text="hello", language="vi")

        assert result == "xin chao"
        translate_service._agent.run.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_translate_file(self, translate_service: TranslateService) -> None:
        upload_file = make_upload_file(
            content_type="application/zip", file_bytes=b"dummy"
        )
        translate_service.doc_handler.is_supported = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="Unsupported file type"):
            await translate_service.translate_file(file=upload_file, language="vi")

