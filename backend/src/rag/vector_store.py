"""
Vector Store - FAISS-based vector storage with embedding & reranking.
"""

import json
import os
import pickle
from datetime import datetime
from typing import List, Tuple

import numpy as np

from src.rag.config import (
    CHUNKS_FILE,
    EMBEDDING_MODEL,
    INDEX_FILE,
    STORAGE_DIR,
    TOP_K_RERANK,
    TOP_K_RETRIEVE,
    TRACKER_FILE,
)
from src.rag.file_processor import chunk_text_recursive, get_file_hash, read_file

# ═══════════════════════════════════════════════════════════
# LAZY-LOADED MODEL SINGLETONS
# ═══════════════════════════════════════════════════════════
_embedder = None
_reranker = None


def get_embedder():
    """Lazy-load the sentence-transformers embedding model."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        print("📥 Loading Embedding model...")
        _embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        print("✅ Embedding ready (CPU)")
    return _embedder


def get_reranker():
    """Lazy-load FlashRank reranker."""
    global _reranker
    if _reranker is None:
        from flashrank import Ranker

        print("📥 Loading FlashRank...")
        _reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=STORAGE_DIR)
        print("✅ FlashRank ready (ONNX)")
    return _reranker


# ═══════════════════════════════════════════════════════════
# EMBEDDING HELPERS
# ═══════════════════════════════════════════════════════════
def embed_texts(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """Embed a list of text chunks."""
    embedder = get_embedder()
    return embedder.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )


def embed_query(query: str) -> np.ndarray:
    """Embed a single query."""
    embedder = get_embedder()
    return embedder.encode([query], normalize_embeddings=True)[0]


def rerank(
    query: str, chunks: List[str], top_k: int = TOP_K_RERANK
) -> List[Tuple[str, float]]:
    """Rerank retrieved chunks using FlashRank."""
    if not chunks:
        return []

    from flashrank import RerankRequest

    ranker = get_reranker()
    passages = [{"text": chunk} for chunk in chunks]
    request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(request)
    return [(r["text"], r["score"]) for r in results[:top_k]]


# ═══════════════════════════════════════════════════════════
# VECTOR STORE
# ═══════════════════════════════════════════════════════════
class VectorStore:
    """FAISS-based vector store for document chunks."""

    def __init__(self):
        self.index = None
        self.chunks: List[str] = []
        self.chunk_metadata: List[dict] = []
        self.files: dict = {}

        os.makedirs(STORAGE_DIR, exist_ok=True)
        self.load()

    def load(self) -> bool:
        """Load persisted index, chunks, and file tracker."""
        try:
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, "rb") as f:
                    self.index = pickle.load(f)

            if os.path.exists(CHUNKS_FILE):
                with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.chunk_metadata = data.get("metadata", [])

            if os.path.exists(TRACKER_FILE):
                with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                    self.files = json.load(f)

            return True
        except Exception as e:
            print(f"Load error: {e}")
            return False

    def save(self):
        """Persist index, chunks, and file tracker to disk."""
        with open(INDEX_FILE, "wb") as f:
            pickle.dump(self.index, f)

        with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"chunks": self.chunks, "metadata": self.chunk_metadata},
                f,
                ensure_ascii=False,
                indent=2,
            )

        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(self.files, f, ensure_ascii=False, indent=2)

    def add_file(self, filepath: str, filename: str) -> int:
        """Index a file: read, chunk, embed, and add to FAISS."""
        import faiss

        text = read_file(filepath)
        chunks = chunk_text_recursive(text)

        if not chunks:
            return 0

        embeddings = embed_texts(chunks)
        dim = embeddings.shape[1]

        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(embeddings.astype("float32"))

        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_metadata.append({"source": filename})

        self.files[filename] = {
            "hash": get_file_hash(filepath),
            "chunks": len(chunks),
            "indexed_at": datetime.now().isoformat(),
        }

        self.save()
        return len(chunks)

    def search(self, query: str, top_k: int = TOP_K_RETRIEVE) -> List[str]:
        """Search for the most similar chunks to the query."""
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = embed_query(query).reshape(1, -1).astype("float32")
        scores, indices = self.index.search(
            query_embedding, min(top_k, self.index.ntotal)
        )

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])

        return results

    def get_stats(self) -> dict:
        """Return index statistics."""
        return {
            "files": len(self.files),
            "chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
        }

    def get_file_list(self) -> dict:
        """Return the tracked files dictionary."""
        return self.files
