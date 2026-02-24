from kreuzberg import ExtractionResult, extract_bytes, extract_file


class DocumentHandler:
    """Async document handler."""

    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/png",
        "image/jpeg",
    }

    async def extract_from_bytes(self, data: bytes, mime_type: str) -> str:
        """Extract text from bytes (async)."""
        result: ExtractionResult = await extract_bytes(data, mime_type)
        return result.content

    async def extract_from_file(self, file_path: str) -> str:
        """Extract text from file path (async)."""
        result: ExtractionResult = await extract_file(file_path)
        return result.content

    def is_supported(self, mime_type: str) -> bool:
        """Check if MIME type is supported."""
        return mime_type in self.SUPPORTED_MIME_TYPES

    async def get_metadata(self, data: bytes, mime_type: str) -> dict:
        """Get document metadata."""
        result = await extract_bytes(data, mime_type)
        return {
            "page_count": result.get_page_count(),
            "detected_language": result.get_detected_language(),
            "mime_type": result.mime_type,
        }

    async def extract_page(self, data: bytes, mime_type: str, page_num: int) -> str:
        """Extract text from specific page."""
        result = await extract_bytes(data, mime_type)
        if result.pages and page_num < len(result.pages):
            return result.pages[page_num].content
        return ""
