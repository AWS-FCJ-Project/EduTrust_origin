from typing import Any, Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer
from src.document_search.vector_store import VectorStore


class DocumentSearchService:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        relevance_threshold: float = 1.7,
    ):
        self.model_name = model_name
        self.relevance_threshold = relevance_threshold
        self.model = SentenceTransformer(model_name)
        self.vector_store = VectorStore()

    async def get_embedding(self, text: str) -> np.ndarray:
        embedding = self.model.encode([text])[0]
        return np.array(embedding)

    async def process_document(self, filename: str) -> bool:
        try:
            if not filename:
                return False

            vector = await self.get_embedding(filename)
            metadata_list = [{"filename": filename, "content": filename}]
            self.vector_store.add_embeddings(vector.reshape(1, -1), metadata_list)
            return True
        except Exception as e:
            print(f"Error processing title '{filename}': {str(e)}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            if not query:
                return []

            query_embedding = await self.get_embedding(query)
            raw_results = self.vector_store.search(
                query_embedding.reshape(1, -1), top_k
            )

            return [
                res for res in raw_results if res["score"] <= self.relevance_threshold
            ]
        except Exception as e:
            print(f"Error searching titles for query '{query}': {str(e)}")
            return []
