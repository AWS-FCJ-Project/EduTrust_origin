from pydantic import BaseModel
from typing import Optional


class RagQueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class RagQueryResponse(BaseModel):
    answer: str
    sources_used: int  # so luong context chunks da dung


class RagIndexResponse(BaseModel):
    success: bool
    filename: str
    chunks_indexed: int
    message: str


class RagStatusResponse(BaseModel):
    ready: bool
    total_chunks: int
    cached_queries: int
    index_type: str
    device: str
    llm_loaded: bool
