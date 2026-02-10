"""
RAG API Routes - Upload, query, manage documents.
"""

import os
import time
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.rag.config import SUPPORTED_EXTENSIONS, UPLOADS_DIR
from src.rag.engine import RAGEngine
from src.schemas.rag_schema import (
    RAGFileInfo,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGStatsResponse,
    RAGUploadResponse,
)

router = APIRouter(prefix="/rag", tags=["RAG"])

# Singleton RAG engine — initialized lazily
_rag_engine: RAGEngine = None


def get_rag_engine() -> RAGEngine:
    """Get or create the RAG engine singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document (PDF, TXT, MD, CSV)."""
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}",
        )

    # Save file
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    filepath = os.path.join(UPLOADS_DIR, file.filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Index file
    try:
        rag = get_rag_engine()
        start_time = time.time()
        chunks = rag.index_file(filepath, file.filename)
        elapsed = time.time() - start_time

        return RAGUploadResponse(
            filename=file.filename,
            chunks=chunks,
            status=f"Indexed successfully in {elapsed:.1f}s",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """Query the RAG system with automatic routing."""
    try:
        rag = get_rag_engine()
        answer, mode = await rag.query_with_mode(request.question)
        return RAGQueryResponse(answer=answer, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/stats", response_model=RAGStatsResponse)
async def get_stats():
    """Get RAG index statistics."""
    rag = get_rag_engine()
    stats = rag.get_stats()
    return RAGStatsResponse(**stats)


@router.get("/files", response_model=List[RAGFileInfo])
async def get_files():
    """List all indexed files."""
    rag = get_rag_engine()
    files = rag.get_files()
    return [
        RAGFileInfo(
            filename=name,
            chunks=info.get("chunks", 0),
            indexed_at=info.get("indexed_at", ""),
        )
        for name, info in files.items()
    ]


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """
    Delete a file from the index.
    Note: This removes the file record but requires re-indexing
    to fully rebuild the FAISS index without the file's chunks.
    """
    rag = get_rag_engine()
    files = rag.get_files()

    if filename not in files:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    # Remove from tracker
    del rag.vector_store.files[filename]
    rag.vector_store.save()

    # Remove uploaded file
    filepath = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    return {"message": f"File '{filename}' removed from index", "status": "deleted"}
