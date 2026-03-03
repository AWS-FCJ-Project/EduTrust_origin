import logging
from typing import List, Optional

from src.rag.file_processor import FileProcessor
from src.rag.llm_client import LLMClient
from src.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RagService:
    """
    Dich vu RAG chinh: ket hop FileProcessor, VectorStore va LLMClient.
    Duoc khoi tao mot lan trong lifespan cua FastAPI va tai su dung.
    """

    def __init__(self):
        self.file_processor = FileProcessor()
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """
        Load FAISS index tu disk neu co san.
        Embedding va reranker model duoc load lazily khi can.
        """
        loaded = self.vector_store.load_or_skip()
        if loaded:
            logger.info("RagService: index loaded from disk.")
        else:
            logger.info("RagService: no existing index found, ready to accept uploads.")

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def index_file(self, filename: str) -> int:
        """
        Doc file tu uploads/, chunk, va them vao vector store.
        Tra ve so luong chunks da them.
        """
        chunks = await self.file_processor.process_file(filename)
        if self.vector_store.is_ready():
            self.vector_store.add_chunks(chunks)
        else:
            self.vector_store.build_index(chunks)
        safe_log_name = filename.replace("\n", "").replace("\r", "")
        logger.info("Indexed '%s' — %d chunks.", safe_log_name, len(chunks))
        return len(chunks)

    async def index_bytes(
        self, data: bytes, mime_type: str, name: str = "upload"
    ) -> int:
        """
        Nhan du lieu bytes (tu upload API), chunk, va index.
        """
        chunks = await self.file_processor.process_bytes(data, mime_type)
        if self.vector_store.is_ready():
            self.vector_store.add_chunks(chunks)
        else:
            self.vector_store.build_index(chunks)
        safe_log_name = name.replace("\n", "").replace("\r", "")
        logger.info("Indexed bytes (%s) — %d chunks.", safe_log_name, len(chunks))
        return len(chunks)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def ask(self, query: str) -> str:
        """
        Thuc hien RAG pipeline: retrieve context → sinh cau tra loi.
        """
        contexts = self.vector_store.retrieve(query)
        if not contexts:
            return "Hien tai chua co tai lieu nao duoc index. Vui long upload tai lieu truoc."

        answer = self.llm_client.generate_answer(query, contexts)
        return answer

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        stats = self.vector_store.get_stats()
        stats["llm_loaded"] = self.llm_client.is_loaded()
        return stats


__all__ = ["RagService"]
