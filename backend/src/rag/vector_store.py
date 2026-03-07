import json
import logging
import os
from typing import List, Optional, Tuple

import faiss
import numpy as np
from opik import track
from sentence_transformers import CrossEncoder, SentenceTransformer
from src.rag.config import (
    BATCH_SIZE,
    DEVICE,
    EMBEDDING_MODEL,
    INDEX_PATH,
    META_PATH,
    NLIST,
    NPROBE,
    RERANKER_MODEL,
    TOP_K_RERANK,
    TOP_K_RETRIEVE,
)

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS IVFFlat vector store ket hop voi cross-encoder reranker va query cache.
    """

    def __init__(self):
        self._embed_model: Optional[SentenceTransformer] = None
        self._reranker: Optional[CrossEncoder] = None
        self._index: Optional[faiss.Index] = None
        self._chunks: List[str] = []
        self._query_cache: dict = {}

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    @property
    def embed_model(self) -> SentenceTransformer:
        if self._embed_model is None:
            logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self._embed_model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)
        return self._embed_model

    @property
    def reranker(self) -> CrossEncoder:
        if self._reranker is None:
            logger.info(f"Loading reranker model: {RERANKER_MODEL}")
            self._reranker = CrossEncoder(RERANKER_MODEL, device=DEVICE)
        return self._reranker

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Tra ve True neu index da duoc build va co chunks."""
        return self._index is not None and len(self._chunks) > 0

    def load_or_skip(self) -> bool:
        """
        Thu load index tu disk. Tra ve True neu thanh cong.
        """
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            try:
                logger.info("Loading existing FAISS index from disk...")
                self._index = faiss.read_index(INDEX_PATH)
                with open(META_PATH, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)
                logger.info(f"Loaded {len(self._chunks)} chunks from disk.")
                return True
            except Exception as e:
                logger.warning(f"Failed to load index: {e}")
        return False

    def build_index(self, chunks: List[str]) -> None:
        """
        Build FAISS IVFFlat index tu danh sach chunks.
        Tu dong luu xuong disk sau khi build.
        """
        if not chunks:
            logger.warning("No chunks provided, skipping index build.")
            return

        logger.info(f"Building FAISS index for {len(chunks)} chunks...")
        self._chunks = chunks
        self._query_cache.clear()  # Reset cache khi index moi

        embeddings = self._embed_chunks(chunks)
        dim = embeddings.shape[1]
        n = len(chunks)

        # FAISS khuyen nghi it nhat 39*nlist training points.
        # Neu du lon thi dung IVFFlat, nguoc lai dung IndexFlatIP.
        min_for_ivf = NLIST * 39
        if n >= min_for_ivf:
            nlist = NLIST
            quantizer = faiss.IndexFlatIP(dim)
            self._index = faiss.IndexIVFFlat(
                quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT
            )
            self._index.train(embeddings)
            self._index.nprobe = NPROBE
        else:
            # Du lieu chua du de dung IVF, dung flat index
            self._index = faiss.IndexFlatIP(dim)

        self._index.add(embeddings)
        self._save_to_disk()
        logger.info("FAISS index built and saved.")

    def add_chunks(self, new_chunks: List[str]) -> None:
        """
        Them chunks moi vao index hien tai (incremental indexing).
        """
        if not new_chunks:
            return

        combined = self._chunks + new_chunks
        self.build_index(combined)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    @track(name="retrieve_context")
    def retrieve(self, query: str) -> List[str]:
        """
        Tim kiem va rerank: tra ve top-K contexts phu hop nhat voi query.
        Ket qua duoc cache theo query string.
        """
        if query in self._query_cache:
            logger.debug("Cache hit for query.")
            return self._query_cache[query]

        if not self.is_ready():
            logger.warning("Index not ready, returning empty context.")
            return []

        # Embed query
        query_embedding = self.embed_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # FAISS search
        k = min(TOP_K_RETRIEVE, len(self._chunks))
        _, idxs = self._index.search(query_embedding, k)
        candidates = [self._chunks[i] for i in idxs[0] if i < len(self._chunks)]

        # Cross-encoder rerank
        top_contexts = self._rerank(query, candidates)

        # Cache va tra ve
        self._query_cache[query] = top_contexts
        return top_contexts

    def get_stats(self) -> dict:
        return {
            "ready": self.is_ready(),
            "total_chunks": len(self._chunks),
            "cached_queries": len(self._query_cache),
            "index_type": type(self._index).__name__ if self._index else "None",
            "device": DEVICE,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _embed_chunks(self, chunks: List[str]) -> np.ndarray:
        return self.embed_model.encode(
            chunks,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    def _rerank(self, query: str, candidates: List[str]) -> List[str]:
        if not candidates:
            return []
        pairs = [[query, c] for c in candidates]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [x[0] for x in ranked[:TOP_K_RERANK]]

    def _save_to_disk(self) -> None:
        faiss.write_index(self._index, INDEX_PATH)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(self._chunks, f, ensure_ascii=False)
        logger.info(f"Index saved to {INDEX_PATH}")
