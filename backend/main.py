"""
FastAPI backend for the Indian Law RAG system.
Serves the retrieval-augmented generation API and document management.
"""
import os
import logging
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import UPLOAD_DIR, MAX_CHAT_HISTORY
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
    title="Nyaya AI — Indian Law RAG API",
    description="Production-grade Retrieval-Augmented Generation for Indian legal documents",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Error Handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
        },
    )


# ── Request / Response Models ──────────────────────────────────
class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = []


class AskResponse(BaseModel):
    answer: str
    confidence: float = 0.0


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
    version: str = "2.0.0"


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

    # Convert chat history to plain dicts, limit to MAX_CHAT_HISTORY
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in req.chat_history[-MAX_CHAT_HISTORY:]
    ] if req.chat_history else None

    result = pipeline.ask(req.question, chat_history=history)

    return AskResponse(
        answer=result["answer"],
        confidence=result.get("confidence", 0.0),
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get knowledge base statistics."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not ready")
    stats = vector_store.stats()
    return StatsResponse(**stats)


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(files: list[UploadFile] = File(...)):
    """Upload and ingest multiple files (PDF or JSON) into the knowledge base."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not ready")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    total_chunks_added = 0
    total_chunks = 0
    processed_count = 0
    skipped_count = 0

    for file in files:
        filename = file.filename.lower() if file.filename else ""
        if not filename.endswith(".pdf") and not filename.endswith(".json"):
            continue

        dest = UPLOAD_DIR / file.filename
        with open(dest, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        logger.info("📄 Uploaded %s → %s", file.filename, dest)

        if filename.endswith(".pdf"):
            result = vector_store.ingest_pdf(dest)
        else:
            result = vector_store.ingest_json(dest)

        if result.get("status") == "success":
            total_chunks_added += result.get("chunks_added", 0)
            total_chunks = result.get("total_chunks", 0)
            processed_count += 1
        elif result.get("status") == "skipped":
            skipped_count += 1

    if processed_count == 0 and skipped_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No valid PDF or JSON files were uploaded",
        )

    # Rebuild BM25 index after new documents
    if processed_count > 0 and pipeline:
        try:
            pipeline.retriever.build_bm25_index()
        except Exception as e:
            logger.warning("BM25 rebuild failed (non-fatal): %s", e)

    status = "success" if processed_count > 0 else "skipped"
    messages = []
    if processed_count > 0:
        messages.append(f"Successfully processed {processed_count} files.")
    if skipped_count > 0:
        messages.append(f"Skipped {skipped_count} files (already indexed).")

    return UploadResponse(
        status=status,
        message=" ".join(messages),
        chunks_added=total_chunks_added,
        total_chunks=total_chunks,
    )


# ── Run ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
