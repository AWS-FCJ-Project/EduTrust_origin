"""
RAG Schemas - Request and Response models for RAG API endpoints.
"""

from typing import Optional

from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    question: str
    mode: Optional[str] = None  # auto, rag_lite, rag_pro, llm_only


class RAGQueryResponse(BaseModel):
    answer: str
    mode: str  # rag_lite, rag_pro, llm_only


class RAGUploadResponse(BaseModel):
    filename: str
    chunks: int
    status: str


class RAGStatsResponse(BaseModel):
    files: int
    chunks: int
    index_size: int


class RAGFileInfo(BaseModel):
    filename: str
    chunks: int
    indexed_at: str
