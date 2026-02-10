"""
RAG Configuration
Centralized configuration for the RAG system.
"""

import os

# ═══════════════════════════════════════════════════════════
# STORAGE PATHS
# ═══════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

INDEX_FILE = os.path.join(STORAGE_DIR, "faiss_index.pkl")
CHUNKS_FILE = os.path.join(STORAGE_DIR, "chunks.json")
TRACKER_FILE = os.path.join(STORAGE_DIR, "files.json")

SUPPORTED_EXTENSIONS = [".txt", ".md", ".csv", ".pdf"]

# ═══════════════════════════════════════════════════════════
# CHUNKING CONFIG
# ═══════════════════════════════════════════════════════════
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# ═══════════════════════════════════════════════════════════
# EMBEDDING CONFIG
# ═══════════════════════════════════════════════════════════
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ═══════════════════════════════════════════════════════════
# RETRIEVAL CONFIG
# ═══════════════════════════════════════════════════════════
TOP_K_RETRIEVE = 20
TOP_K_RERANK = 3

# ═══════════════════════════════════════════════════════════
# CONTEXT CONFIG
# ═══════════════════════════════════════════════════════════
MAX_CONTEXT_TOKENS = 1200
TOKENS_PER_CHAR = 0.25

# ═══════════════════════════════════════════════════════════
# LLM CONFIG
# ═══════════════════════════════════════════════════════════
LLM_MAX_TOKENS = 700
LLM_TEMPERATURE = 0.21

# ═══════════════════════════════════════════════════════════
# ROUTING CONFIG
# ═══════════════════════════════════════════════════════════
SIMILARITY_THRESHOLD = 0.5

RAG_PRO_KEYWORDS = [
    "theo tài liệu", "trong sách", "trong tài liệu", "theo sách",
    "chương", "trang", "section", "chapter", "page",
    "được định nghĩa", "được mô tả", "được giải thích",
    "so sánh trong tài liệu", "trích dẫn", "quote",
    "theo như", "dựa theo", "như đã nói",
]

# ═══════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════
HYBRID_PROMPT = """Based on the following context, answer the question.

RULES:
1. Prefer using the provided context if relevant
2. If context is insufficient, you may use general AI knowledge
3. Clearly indicate when the answer is based on general knowledge
4. Answer in the same language as the question

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

STRICT_PROMPT = """Based on the following context, answer the question accurately.

IMPORTANT RULES:
1. ONLY use information from the context below
2. If the answer is NOT in the context, say "Tôi không tìm thấy thông tin này trong tài liệu."
3. Be specific and cite which part of the context you're using
4. Answer in the same language as the question

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

NO_CONTEXT_PROMPT = """Answer the following question using your general AI knowledge.

RULES:
1. Be accurate and educational
2. Answer in the same language as the question
3. If you're unsure, indicate your uncertainty

QUESTION: {question}

ANSWER:"""
