import logging
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

from src.schemas.rag_schema import (
    RagIndexResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagStatusResponse,
)
from src.state import get_rag_service

UPLOADS_DIR = Path("uploads").resolve()

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
        original_filename = file.filename or "upload"

        # Loại bỏ path injection
        safe_filename = Path(original_filename).name

        # Tạo thư mục nếu chưa tồn tại
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        # Tạo full path và verify không escape khỏi uploads
        save_path = (UPLOADS_DIR / safe_filename).resolve()

        if not str(save_path).startswith(str(UPLOADS_DIR)):
            raise HTTPException(status_code=400, detail="Invalid filename.")

        # Save file (async to avoid blocking event loop)
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)

        # Index trực tiếp từ bytes
        chunks_count = await service.index_bytes(content, mime_type, safe_filename)

        return RagIndexResponse(
            success=True,
            filename=safe_filename,
            chunks_indexed=chunks_count,
            message=f"Successfully indexed {chunks_count} chunks from '{safe_filename}'.",
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"RAG index error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to index file: {str(e)}")
