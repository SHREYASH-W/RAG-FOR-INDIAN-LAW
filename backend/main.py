"""
FastAPI backend for the Indian Law RAG system.
Serves the retrieval-augmented generation API and document management.
"""
import os
import logging
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import UPLOAD_DIR
from rag_engine import VectorStore, Reranker, RAGPipeline

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-18s │ %(levelname)-5s │ %(message)s",
)
logger = logging.getLogger("indian_law_api")

# Suppress noisy ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"
os.environ["OTEL_SDK_DISABLED"] = "true"

# ── Globals (populated at startup) ─────────────────────────────
vector_store: VectorStore | None = None
reranker: Reranker | None = None
pipeline: RAGPipeline | None = None


# ── Lifespan ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, reranker, pipeline
    logger.info("🚀 Loading models and connecting to ChromaDB…")
    vector_store = VectorStore()
    reranker = Reranker()
    pipeline = RAGPipeline(vector_store, reranker)
    logger.info("✅ All systems ready")
    yield
    logger.info("🛑 Shutting down")


# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="Indian Law RAG API",
    description="Retrieval-Augmented Generation for Indian legal documents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────
class AskRequest(BaseModel):
    question: str


class SourceInfo(BaseModel):
    act_name: str | None = None
    part: str | None = None
    chapter: str | None = None
    article: str | None = None
    section: str | None = None
    page: int | None = None
    score: float | None = None
    excerpt: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = []


class StatsResponse(BaseModel):
    total_chunks: int
    document_count: int
    documents: list[str]


class UploadResponse(BaseModel):
    status: str
    message: str
    chunks_added: int
    total_chunks: int = 0


class HealthResponse(BaseModel):
    status: str
    chromadb_chunks: int


# ── Endpoints ──────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    count = vector_store.collection.count() if vector_store else 0
    return HealthResponse(status="ok", chromadb_chunks=count)


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    """Ask a question about Indian law."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not ready")

    logger.info("❓ Question: %s", req.question[:100])
    result = pipeline.ask(req.question)
    return AskResponse(
        answer=result["answer"],
        sources=[SourceInfo(**s) for s in result["sources"]],
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get knowledge base statistics."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    stats = vector_store.stats()
    return StatsResponse(**stats)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and ingest a new file (PDF or JSON) into the knowledge base."""
    filename = file.filename.lower() if file.filename else ""
    if not filename.endswith(".pdf") and not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only PDF and JSON files are accepted")

    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not ready")

    # Save uploaded file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    logger.info("📄 Uploaded %s → %s", file.filename, dest)

    # Ingest into ChromaDB
    if filename.endswith(".pdf"):
        result = vector_store.ingest_pdf(dest)
    else:
        result = vector_store.ingest_json(dest)
    return UploadResponse(**result)


# ── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
