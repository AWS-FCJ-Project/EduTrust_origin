import os
from typing import Any, Dict, List

import boto3
from fastapi import UploadFile
from src.app_config import app_config
from src.document_handler.document_handler import DocumentHandler
from src.document_search.vector_store import BM25Store

# =============================================================================
# OLD VECTOR SEARCH CODE (COMMENTED OUT FOR RESTORATION)
# =============================================================================
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from src.document_search.vector_store import VectorStore
#
# class DocumentSearchService:
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2", relevance_threshold: float = 1.7):
#         self.model_name = model_name
#         self.relevance_threshold = relevance_threshold
#         self.model = SentenceTransformer(model_name)
#         self.vector_store = VectorStore()
#
#     async def get_embedding(self, text: str) -> np.ndarray:
#         embedding = self.model.encode([text])[0]
#         return np.array(embedding)
#
#     async def process_document(self, filename: str) -> bool:
#         try:
#             if not filename: return False
#             vector = await self.get_embedding(filename)
#             metadata_list = [{"filename": filename, "content": filename}]
#             self.vector_store.add_embeddings(vector.reshape(1, -1), metadata_list)
#             return True
#         except Exception as e:
#             print(f"Error processing title '{filename}': {str(e)}")
#             return False
#
#     async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
#         try:
#             if not query: return []
#             query_embedding = await self.get_embedding(query)
#             raw_results = self.vector_store.search(query_embedding.reshape(1, -1), top_k)
#             return [res for res in raw_results if res["score"] <= self.relevance_threshold]
#         except Exception as e:
#             print(f"Error searching titles for query '{query}': {str(e)}")
#             return []
# =============================================================================


class DocumentSearchService:
    def __init__(self):
        self.bm25_store = BM25Store()
        self.doc_handler = DocumentHandler()
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION,
        )
        self.bucket_name = app_config.S3_BUCKET_NAME

    async def process_document(self, file: UploadFile) -> bool:
        try:
            filename = file.filename
            if not filename:
                return False

            # 1. Read file content
            content_bytes = await file.read()

            # 2. Upload original file to regular S3
            s3_key = f"uploads/{filename}"
            print(f"Uploading original file to S3: {self.bucket_name}/{s3_key}")
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=s3_key, Body=content_bytes
            )

            # 3. Extract text from content
            mime_type = file.content_type or "application/pdf"
            print(f"Extracting text from {filename} (MIME: {mime_type})...")
            text_content = await self.doc_handler.extract_from_bytes(
                content_bytes, mime_type
            )

            if not text_content:
                print(f"WARNING: No text extracted from {filename}")
                text_content = filename  # Fallback to filename if text extraction fails

            # 4. Add to BM25 index
            # Store a snippet for the search result display
            snippet = text_content[:300] + ("..." if len(text_content) > 300 else "")
            metadata = {"filename": filename, "content": snippet, "s3_key": s3_key}

            print(f"Indexing document in BM25: {filename}")
            self.bm25_store.add_document(text_content, metadata)

            # Reset file cursor just in case
            await file.seek(0)

            return True
        except Exception as e:
            print(f"Error processing document '{file.filename}': {str(e)}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            if not query:
                return []

            print(f"Searching BM25 for query: '{query}'")
            return self.bm25_store.search(query, top_k)
        except Exception as e:
            print(f"Error searching BM25 for query '{query}': {str(e)}")
            return []
