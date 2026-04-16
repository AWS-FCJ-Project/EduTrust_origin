from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from src.document_handler.document_handler import DocumentHandler


@pytest.fixture
def document_handler() -> DocumentHandler:
    return DocumentHandler()


def test_is_supported_checks_known_mime_types(document_handler: DocumentHandler):
    assert document_handler.is_supported("application/pdf") is True
    assert document_handler.is_supported("application/xml") is False


@pytest.mark.asyncio
async def test_extract_from_bytes_returns_result_content(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(content="Extracted from bytes")
    mock_extract = AsyncMock(return_value=mock_result)
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_bytes",
        mock_extract,
    )

    result = await document_handler.extract_from_bytes(b"file", "application/pdf")

    assert result == "Extracted from bytes"
    mock_extract.assert_awaited_once_with(b"file", "application/pdf")


@pytest.mark.asyncio
async def test_extract_from_file_returns_result_content(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(content="Extracted from file")
    mock_extract = AsyncMock(return_value=mock_result)
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_file",
        mock_extract,
    )

    result = await document_handler.extract_from_file("/tmp/demo.pdf")

    assert result == "Extracted from file"
    mock_extract.assert_awaited_once_with("/tmp/demo.pdf")


@pytest.mark.asyncio
async def test_get_metadata_maps_extraction_result(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(
        mime_type="application/pdf",
        get_page_count=lambda: 3,
        get_detected_language=lambda: "en",
    )
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_bytes",
        AsyncMock(return_value=mock_result),
    )

    metadata = await document_handler.get_metadata(b"file", "application/pdf")

    assert metadata == {
        "page_count": 3,
        "detected_language": "en",
        "mime_type": "application/pdf",
    }


@pytest.mark.asyncio
async def test_extract_page_returns_requested_page_content(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(
        pages=[
            SimpleNamespace(content="Page 1"),
            SimpleNamespace(content="Page 2"),
        ]
    )
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_bytes",
        AsyncMock(return_value=mock_result),
    )

    result = await document_handler.extract_page(b"file", "application/pdf", 1)

    assert result == "Page 2"


@pytest.mark.asyncio
async def test_extract_page_returns_empty_when_page_out_of_range(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(pages=[SimpleNamespace(content="Only page")])
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_bytes",
        AsyncMock(return_value=mock_result),
    )

    result = await document_handler.extract_page(b"file", "application/pdf", 5)

    assert result == ""


@pytest.mark.asyncio
async def test_extract_page_returns_empty_when_no_pages(
    document_handler: DocumentHandler, monkeypatch
):
    mock_result = SimpleNamespace(pages=None)
    monkeypatch.setattr(
        "src.document_handler.document_handler.extract_bytes",
        AsyncMock(return_value=mock_result),
    )

    result = await document_handler.extract_page(b"file", "application/pdf", 0)

    assert result == ""
