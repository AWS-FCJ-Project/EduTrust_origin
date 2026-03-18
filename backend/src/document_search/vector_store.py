import os
import pickle
from typing import Any, Dict, List, Optional

import faiss
import numpy as np


class VectorStore:
    def __init__(
        self,
        index_path: str = "document_search_index.faiss",
        metadata_path: str = "document_search_metadata.pkl",
    ):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.dimension = 1536  # Default for text-embedding-3-small
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata: List[Dict[str, Any]] = []

        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.load()

    def add_embeddings(
        self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]
    ):
        """Add embeddings and their corresponding metadata to the store."""
        if embeddings.shape[1] != self.dimension:
            # Re-initialize index if dimension changes (though it shouldn't for the same model)
            self.dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

        self.index.add(embeddings.astype("float32"))
        self.metadata.extend(metadata_list)
        self.save()

    def search(
        self, query_embedding: np.ndarray, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for the most similar embeddings and return their metadata with scores."""
        if self.index.ntotal == 0:
            return []

        distances, indices = self.index.search(
            query_embedding.astype("float32"), min(top_k, self.index.ntotal)
        )

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                item = self.metadata[idx].copy()
                item["score"] = float(distances[0][i])
                results.append(item)

        # Sort by score (distance) - lower is better for L2
        return sorted(results, key=lambda x: x["score"])

    def save(self):
        """Save the index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        """Load the index and metadata from disk."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            self.dimension = self.index.d
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
