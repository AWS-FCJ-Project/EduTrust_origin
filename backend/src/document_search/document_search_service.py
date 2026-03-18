import numpy as np
from typing import List, Dict, Any
from litellm import embedding
from src.app_config import app_config
from src.document_search.vector_store import VectorStore

class DocumentSearchService:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.vector_store = VectorStore()
        # Ensure API key is set for litellm if needed
        import os
        if app_config.LITELLM_API_KEY:
            os.environ["OPENAI_API_KEY"] = app_config.LITELLM_API_KEY

    async def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single string using litellm."""
        response = embedding(
            model=self.model_name,
            input=[text]
        )
        return np.array(response['data'][0]['embedding'])

    async def process_document(self, filename: str) -> bool:
        """Embed the filename (title) and save to vector store."""
        try:
            # 1. Embed title
            vector = await self.get_embedding(filename)
            
            # 2. Prepare metadata
            metadata_list = [{
                "filename": filename,
                "content": filename, # Using filename as content since we only search by title
            }]
            
            # 3. Save to vector store
            self.vector_store.add_embeddings(vector.reshape(1, -1), metadata_list)
            return True
            
        except Exception as e:
            print(f"Error processing title: {str(e)}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents by matching the query against their titles."""
        try:
            # 1. Embed query
            query_embedding = await self.get_embedding(query)
            
            # 2. Search vector store
            results = self.vector_store.search(query_embedding.reshape(1, -1), top_k)
            
            return results
        except Exception as e:
            print(f"Error searching titles: {str(e)}")
            return []
