import os

import torch

# ============================
# PATHS
# ============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

INDEX_PATH = os.path.join(STORAGE_DIR, "faiss.index")
META_PATH = os.path.join(STORAGE_DIR, "chunks.json")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ============================
# MODEL CONFIG
# ============================

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
RERANKER_MODEL = os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base")
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

# ============================
# CHUNKING CONFIG
# ============================

CHUNK_SIZE = 500  # tokens per chunk
OVERLAP = 50  # token overlap between consecutive chunks

# ============================
# RETRIEVAL CONFIG
# ============================

BATCH_SIZE = 64  # embedding batch size
TOP_K_RETRIEVE = 8  # number of candidates from FAISS
TOP_K_RERANK = 3  # number of final contexts after reranking
NLIST = 100  # FAISS IVF cluster count
NPROBE = 10  # FAISS IVF search probes

# ============================
# DEVICE
# ============================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
