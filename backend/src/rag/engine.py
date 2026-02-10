"""
RAG Engine - Main orchestrator for the RAG system.
Integrates VectorStore, QuestionRouter, and LLM Client.
"""

from typing import Tuple

from src.rag.config import (
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    RAG_PRO_KEYWORDS,
    SIMILARITY_THRESHOLD,
    TOP_K_RERANK,
    TOP_K_RETRIEVE,
    HYBRID_PROMPT,
    STRICT_PROMPT,
    NO_CONTEXT_PROMPT,
)
from src.rag.llm_client import RAGLLMClient
from src.rag.vector_store import VectorStore, rerank


# ═══════════════════════════════════════════════════════════
# QUESTION ROUTER
# ═══════════════════════════════════════════════════════════
class QuestionRouter:
    """Routes questions to the appropriate RAG mode."""

    def classify(self, question: str, context_score: float = 0.0) -> str:
        """Classify question into rag_pro, rag_lite, or llm_only."""
        question_lower = question.lower()

        for keyword in RAG_PRO_KEYWORDS:
            if keyword in question_lower:
                return "rag_pro"

        if context_score < SIMILARITY_THRESHOLD:
            return "llm_only"

        return "rag_lite"

    def get_prompt(self, mode: str, question: str, context: str) -> str:
        """Get the appropriate prompt template for the mode."""
        if mode == "rag_pro":
            return STRICT_PROMPT.format(context=context, question=question)
        elif mode == "rag_lite":
            return HYBRID_PROMPT.format(context=context, question=question)
        else:
            return NO_CONTEXT_PROMPT.format(question=question)


# ═══════════════════════════════════════════════════════════
# RAG ENGINE
# ═══════════════════════════════════════════════════════════
class RAGEngine:
    """
    Main RAG Engine with hybrid routing.

    Architecture:
        User Question
              │
              ▼
        [Question Router]
              │
        ┌─────┴─────────────┐
        │                   │
        ▼                   ▼
      rag_lite           rag_pro
      (fast)             (deep)
        │                   │
        ▼                   ▼
      LLM + Prior      Strict RAG
      Knowledge        (No hallucination)
    """

    def __init__(self, model: str = None):
        """
        Initialize RAG Engine.

        Args:
            model: LLM model name for generation (e.g. 'gpt-4.1-nano').
        """
        self.vector_store = VectorStore()
        self.router = QuestionRouter()
        self.llm = RAGLLMClient(model=model)

    def preload(self):
        """Preload embedding and reranking models."""
        from src.rag.vector_store import get_embedder, get_reranker

        get_embedder()
        get_reranker()

    def index_file(self, filepath: str, filename: str) -> int:
        """
        Index a file into the vector store.

        Args:
            filepath: Path to the file on disk.
            filename: Display name for the file.

        Returns:
            Number of chunks indexed.
        """
        return self.vector_store.add_file(filepath, filename)

    def get_stats(self) -> dict:
        """Return index statistics."""
        return self.vector_store.get_stats()

    def get_files(self) -> dict:
        """Return tracked files."""
        return self.vector_store.get_file_list()

    async def query(self, question: str) -> str:
        """Query the RAG system and return the answer."""
        answer, _ = await self.query_with_mode(question)
        return answer

    async def query_with_mode(self, question: str) -> Tuple[str, str]:
        """
        Query the RAG system and return (answer, mode).

        The routing logic:
        1. Check for RAG Pro keywords → force rag_pro mode
        2. Retrieve documents from vector store
        3. Rerank retrieved documents
        4. If top score < threshold → llm_only
        5. Otherwise → rag_lite (hybrid)
        """
        # Get initial classification
        initial_mode = self.router.classify(question)

        # Get context from vector store
        retrieved = self.vector_store.search(question, TOP_K_RETRIEVE)

        if not retrieved:
            # No documents indexed — use LLM only
            mode = "llm_only"
            prompt = self.router.get_prompt(mode, question, "")
        else:
            # Rerank
            reranked = rerank(question, retrieved, TOP_K_RERANK)

            if not reranked:
                mode = "llm_only"
                prompt = self.router.get_prompt(mode, question, "")
            else:
                # Get top score for routing decision
                top_score = reranked[0][1]

                # Re-evaluate mode based on score
                if initial_mode == "rag_pro":
                    mode = "rag_pro"
                elif top_score < SIMILARITY_THRESHOLD:
                    mode = "llm_only"
                else:
                    mode = "rag_lite"

                # Build context
                context_parts = []
                for i, (chunk, score) in enumerate(reranked, 1):
                    context_parts.append(f"[Đoạn {i}]\n{chunk}")
                context = "\n\n---\n\n".join(context_parts)

                prompt = self.router.get_prompt(mode, question, context)

        # Generate answer via GPT API
        system_prompt = (
            "You are a helpful educational AI assistant. "
            "Be accurate, clear, and helpful."
        )

        answer = await self.llm.generate(
            prompt,
            system_prompt=system_prompt,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
        )

        return answer, mode
