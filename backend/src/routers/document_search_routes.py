from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.document_search.document_search_service import DocumentSearchService

router = APIRouter(prefix="/document-search", tags=["Document Search"])
search_service = DocumentSearchService()


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResult(BaseModel):
    filename: str
    content: str
    score: float


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Simple check for PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # In this simplified version, we only index the filename (title)
    success = await search_service.process_document(file.filename)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to index document title.")

    return {"message": f"Document title '{file.filename}' indexed successfully."}


@router.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    results = await search_service.search(request.query, request.top_k)
    return [
        SearchResult(
            filename=res["filename"], content=res["content"], score=res["score"]
        )
        for res in results
    ]
