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
async def upload_documents(files: List[UploadFile] = File(...)):
    indexed_files = []
    failed_files = []

    for file in files:
        if not file.filename.endswith(".pdf"):
            failed_files.append(
                {"filename": file.filename, "reason": "Only PDF files are supported."}
            )
            continue

        success = await search_service.process_document(file.filename)

        if success:
            indexed_files.append(file.filename)
        else:
            failed_files.append(
                {"filename": file.filename, "reason": "Failed to index document title."}
            )

    return {
        "message": f"Processed {len(files)} files.",
        "indexed_count": len(indexed_files),
        "indexed_files": indexed_files,
        "failed_count": len(failed_files),
        "failed_files": failed_files,
    }


@router.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    results = await search_service.search(request.query, request.top_k)
    return [
        SearchResult(
            filename=res["filename"], content=res["content"], score=res["score"]
        )
        for res in results
    ]
