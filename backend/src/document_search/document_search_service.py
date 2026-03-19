from typing import Any, Dict, List

import numpy as np
from litellm import completion, embedding
from src.app_config import app_config
from src.document_search.vector_store import VectorStore


class DocumentSearchService:
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        relevance_threshold: float = 1.4,
    ):
        self.model_name = model_name
        self.relevance_threshold = relevance_threshold
        self.vector_store = VectorStore()
        import os

        if app_config.LITELLM_API_KEY:
            os.environ["OPENAI_API_KEY"] = app_config.LITELLM_API_KEY

    async def get_embedding(self, text: str) -> np.ndarray:
        response = embedding(model=self.model_name, input=[text])
        return np.array(response["data"][0]["embedding"])

    async def rerank_results(
        self, query: str, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not results:
            return []

        titles = [res["filename"] for res in results]
        prompt = f"""
        User Query: "{query}"
        List of Document Titles: {titles}

        Which of these titles are semantically relevant to the user's query? 
        Return ONLY the list of indices (0-indexed) that are truly relevant, separated by commas. 
        If none are relevant, return "NONE".
        Example: 0, 2
        """

        try:
            response = completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0,
            )
            content = response.choices[0].message.content.strip().upper()

            if content == "NONE":
                return []

            indices = [
                int(i.strip()) for i in content.split(",") if i.strip().isdigit()
            ]
            return [results[i] for i in indices if i < len(results)]
        except Exception as e:
            print(f"Error during GPT reranking: {str(e)}")
            return results

    async def process_document(self, filename: str) -> bool:
        try:
            if not filename:
                return False

            vector = await self.get_embedding(filename)

            if vector is None or vector.size == 0:
                print(f"Error: Could not generate embedding for {filename}")
                return False

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
            if query_embedding is None or query_embedding.size == 0:
                return []

            raw_results = self.vector_store.search(
                query_embedding.reshape(1, -1), top_k
            )

            if not raw_results:
                return []

            avg_score = sum(res["score"] for res in raw_results) / len(raw_results)

            if avg_score < 1.2:
                return [
                    res
                    for res in raw_results
                    if res["score"] <= self.relevance_threshold
                ]

            candidates = [
                res for res in raw_results if res["score"] <= self.relevance_threshold
            ]

            if not candidates:
                return []

            final_results = await self.rerank_results(query, candidates)
            return final_results

        except Exception as e:
            print(f"Error searching titles for query '{query}': {str(e)}")
            return []
