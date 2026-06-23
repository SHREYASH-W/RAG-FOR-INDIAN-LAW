"""
Configuration for the Indian Law RAG backend.
All constants match the original Kaggle notebook for ChromaDB compatibility.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # d:\indian rag
CHROMA_DIR = BASE_DIR / "chroma_db"
PDF_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "data"                              # uploaded PDFs go here too

# ── Embedding & Reranking Models ───────────────────────────────
EMBED_MODEL = "BAAI/bge-base-en-v1.5"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# ── ChromaDB ───────────────────────────────────────────────────
COLLECTION_NAME = "indian_law"

# ── Chunking ───────────────────────────────────────────────────
CHUNK_SIZE = 350          # words per chunk
CHUNK_OVERLAP = 75        # overlapping words between consecutive chunks

# ── Retrieval ──────────────────────────────────────────────────
TOP_K = 15                # initial retrieval count per search method
RERANK_TOP_N = 5          # final count after reranking

# ── Hybrid Search ──────────────────────────────────────────────
BM25_WEIGHT = 0.4         # weight for BM25 sparse results in RRF
DENSE_WEIGHT = 1.0        # weight for dense vector results in RRF

# ── Query Expansion ────────────────────────────────────────────
QUERY_EXPANSION_ENABLED = True
QUERY_EXPANSION_COUNT = 2  # max number of alternative queries to generate

# ── Contextual Compression ─────────────────────────────────────
COMPRESSION_ENABLED = True

# ── LLM ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 2000

# ── Conversation Memory ───────────────────────────────────────
MAX_CHAT_HISTORY = 10     # max messages to include in context

# ── Act name mapping (kept for backward compat, also in chunker) ──
ACT_MAP = {
    "constitution_of_india.pdf": "Constitution of India",
    "the_bharatiya_nagarik_suraksha_sanhita_2023.pdf":
        "Bharatiya Nagarik Suraksha Sanhita, 2023",
}
