import os
import logging
from typing import List

from src.rag.config import (
    CHUNK_SIZE,
    OVERLAP,
    UPLOADS_DIR,
    EMBEDDING_MODEL,
)
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Xu ly file upload: trich xuat text va chia thanh chunks dua tren tokens.
    Su dung kreuzberg (DocumentHandler) de trich xuat text da duoc tich hop san.
    """

    def __init__(self):
        # Dung tokenizer cua embedding model de chia chunk chinh xac
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_file(self, filename: str) -> List[str]:
        """
        Doc file tu uploads/, trich xuat text, chia chunk.
        Tra ve danh sach cac chunk text.
        """
        file_path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        text = await self._extract_text(file_path)
        chunks = self._chunk_text(text)
        return chunks

    async def process_bytes(self, data: bytes, mime_type: str) -> List[str]:
        """
        Nhan raw bytes + mime_type, trich xuat text, chia chunk.
        Dung khi upload qua API (khong luu file tam).
        """
        from kreuzberg import extract_bytes

        result = await extract_bytes(data, mime_type)
        text = result.content or ""
        return self._chunk_text(text)

    def get_upload_path(self, filename: str) -> str:
        return os.path.join(UPLOADS_DIR, filename)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _extract_text(self, file_path: str) -> str:
        from kreuzberg import extract_file

        result = await extract_file(file_path)
        return result.content or ""

    def _chunk_text(self, text: str) -> List[str]:
        """
        Token-based chunking voi CHUNK_SIZE va OVERLAP.
        Dung tokenizer cua embedding model de dem tokens chinh xac.
        """
        if not text.strip():
            return []

        # encode() khong gioi han max_length — lay toan bo tokens
        tokens = self.tokenizer.encode(
            text,
            add_special_tokens=False,
            max_length=None,
            truncation=False,
        )

        chunks = []
        start = 0
        while start < len(tokens):
            end = start + CHUNK_SIZE
            chunk_tokens = tokens[start:end]
            chunks.append(
                self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            )
            start += CHUNK_SIZE - OVERLAP

        return chunks
