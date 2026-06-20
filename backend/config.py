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
TOP_K = 15                # initial retrieval count
RERANK_TOP_N = 5          # final count after reranking

# ── LLM ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 1500

# ── Act name mapping (matches notebook) ────────────────────────
ACT_MAP = {
    "constitution_of_india.pdf": "Constitution of India",
    "the_bharatiya_nagarik_suraksha_sanhita_2023.pdf":
        "Bharatiya Nagarik Suraksha Sanhita, 2023",
}
