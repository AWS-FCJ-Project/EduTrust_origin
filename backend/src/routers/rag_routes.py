import os
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from src.state import get_rag_service
from src.schemas.rag_schema import (
    RagQueryRequest,
    RagQueryResponse,
    RagIndexResponse,
    RagStatusResponse,
)
from src.rag.config import UPLOADS_DIR

router = APIRouter(prefix="/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=RagStatusResponse)
def rag_status():
    """Trang thai cua RAG index va cac model."""
    try:
        service = get_rag_service()
        return RagStatusResponse(**service.get_status())
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/ask", response_model=RagQueryResponse)
def rag_ask(request: RagQueryRequest):
    """
    Dat cau hoi, RAG pipeline se retrieve context tu tai lieu
    va sinh cau tra loi bang LLM local.
    """
    try:
        service = get_rag_service()
        contexts = service.vector_store.retrieve(request.question)
        answer = service.llm_client.generate_answer(request.question, contexts)
        return RagQueryResponse(answer=answer, sources_used=len(contexts))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"RAG ask error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal RAG error")


@router.post("/index", response_model=RagIndexResponse)
async def rag_index(file: UploadFile = File(...)):
    """
    Upload file (PDF, TXT, DOCX...) de index vao FAISS vector store.
    """
    try:
        service = get_rag_service()

        content = await file.read()
        mime_type = file.content_type or "application/octet-stream"
        filename = file.filename or "upload"

        # Luu file xuong uploads/
        save_path = os.path.join(UPLOADS_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(content)

        # Index tu bytes (khong re-read tu disk)
        chunks_count = await service.index_bytes(content, mime_type, filename)

        return RagIndexResponse(
            success=True,
            filename=filename,
            chunks_indexed=chunks_count,
            message=f"Successfully indexed {chunks_count} chunks from '{filename}'.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"RAG index error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")
