"""
File Processor - Read & Chunk Documents
Supports: PDF, TXT, MD, CSV
"""

import hashlib
import os
from typing import List

from src.rag.config import CHUNK_OVERLAP, CHUNK_SIZE, SEPARATORS


# ═══════════════════════════════════════════════════════════
# FILE READERS
# ═══════════════════════════════════════════════════════════
def read_pdf(file_path: str) -> str:
    """Read PDF file and extract text."""
    import pdfplumber

    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)


def read_text(file_path: str) -> str:
    """Read text file with multiple encoding fallbacks."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8", errors="ignore")


def read_file(file_path: str) -> str:
    """Read file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return read_pdf(file_path)
    return read_text(file_path)


# ═══════════════════════════════════════════════════════════
# TEXT CHUNKING
# ═══════════════════════════════════════════════════════════
def chunk_text_recursive(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: List[str] = None,
) -> List[str]:
    """Recursive Character Text Splitter."""
    if separators is None:
        separators = SEPARATORS.copy()

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    for i, separator in enumerate(separators):
        if separator == "":
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                start = end - chunk_overlap
            return chunks

        if separator in text:
            parts = text.split(separator)
            chunks = []
            current_chunk = ""

            for part in parts:
                part = part.strip()
                if not part:
                    continue

                if len(part) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = ""
                    sub_chunks = chunk_text_recursive(
                        part, chunk_size, chunk_overlap, separators[i + 1 :]
                    )
                    chunks.extend(sub_chunks)
                elif len(current_chunk) + len(separator) + len(part) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
                else:
                    if current_chunk:
                        current_chunk += separator + part
                    else:
                        current_chunk = part

            if current_chunk:
                chunks.append(current_chunk)

            if chunks:
                return chunks

    return [text.strip()] if text.strip() else []


# ═══════════════════════════════════════════════════════════
# FILE HASHING
# ═══════════════════════════════════════════════════════════
def get_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
