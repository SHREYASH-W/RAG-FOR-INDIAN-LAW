"""
RAG Engine — PDF processing, vector store, reranking, and answer generation.
Mirrors the logic from the Kaggle notebook but structured for production use.
"""
import re
import hashlib
import logging
from pathlib import Path
from typing import Optional

import pdfplumber
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder
from groq import Groq

from config import (
    CHROMA_DIR, EMBED_MODEL, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, RERANK_TOP_N,
    RERANK_MODEL, GROQ_API_KEY, GROQ_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, ACT_MAP,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  PDF Processing
# ═══════════════════════════════════════════════════════════════

def _get_act_name(filename: str) -> str:
    """Map a filename to a human-readable act name."""
    return ACT_MAP.get(
        filename.lower(),
        Path(filename).stem.replace("_", " ").title(),
    )


def _extract_metadata(text: str) -> dict:
    """Pull Part / Chapter / Article / Section from a text chunk."""
    meta: dict = {}

    part = re.search(r"PART\s+([IVXLC]+)", text, re.I)
    if part:
        meta["part"] = f"Part {part.group(1)}"

    chapter = re.search(r"CHAPTER\s+([IVXLC]+)", text, re.I)
    if chapter:
        meta["chapter"] = f"Chapter {chapter.group(1)}"

    article = re.search(r"Article\s+(\d+[A-Z]?)", text, re.I)
    if article:
        meta["article"] = article.group(1)

    section = re.search(r"Section\s+(\d+[A-Z]?)", text, re.I)
    if section:
        meta["section"] = section.group(1)

    return meta


def extract_pages(pdf_path: Path) -> list[dict]:
    """Extract text from every page of a PDF."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append({"page": page_num, "text": text.strip()})
    return pages


def chunk_page(page_text: str, page_num: int, source: str) -> list[dict]:
    """Split a page into overlapping word-level chunks with metadata."""
    words = page_text.split()
    chunks = []
    start = 0
    running_meta: dict = {}

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_text = " ".join(words[start:end])

        current = _extract_metadata(chunk_text)
        running_meta.update(current)

        chunks.append({"text": chunk_text, "source": source, "page": page_num, **running_meta})
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def pdf_md5(path: Path) -> str:
    """Compute MD5 hash to detect duplicate PDFs."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════════
#  Vector Store (ChromaDB wrapper)
# ═══════════════════════════════════════════════════════════════

class VectorStore:
    """Manages the ChromaDB collection for Indian law documents."""

    def __init__(self):
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL,
            device="cpu",  # ChromaDB internal embedding — leave on CPU
        )
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB loaded — collection=%s chunks=%d",
            COLLECTION_NAME,
            self.collection.count(),
        )

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """Retrieve top-K chunks via cosine similarity."""
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({
                "text": doc,
                "source": meta.get("source"),
                "act_name": meta.get("act_name"),
                "part": meta.get("part"),
                "chapter": meta.get("chapter"),
                "article": meta.get("article"),
                "section": meta.get("section"),
                "page": meta.get("page"),
                "score": round(1 - dist, 4),
            })
        return hits

    def ingest_pdf(self, pdf_path: Path) -> dict:
        """Ingest a PDF into the vector store. Returns stats dict."""
        md5 = pdf_md5(pdf_path)

        # Dedup check
        existing = self.collection.get(where={"pdf_hash": md5}, limit=1)
        if existing["ids"]:
            return {
                "status": "skipped",
                "message": f"{pdf_path.name} already ingested",
                "chunks_added": 0,
            }

        pages = extract_pages(pdf_path)
        act_name = _get_act_name(pdf_path.name)

        docs, metas, ids = [], [], []
        idx = 0

        for page in pages:
            chunks = chunk_page(page["text"], page["page"], pdf_path.name)
            for c in chunks:
                ids.append(f"{md5}_{idx}")
                docs.append(c["text"])

                meta = {
                    "source": pdf_path.name,
                    "act_name": act_name,
                    "page": int(c.get("page", 0)),
                    "pdf_hash": md5,
                }
                for key in ("part", "chapter", "article", "section"):
                    if c.get(key):
                        meta[key] = str(c[key])

                metas.append(meta)
                idx += 1

        # Batch upsert (500 at a time — ChromaDB best practice)
        for i in range(0, len(ids), 500):
            self.collection.add(
                ids=ids[i : i + 500],
                documents=docs[i : i + 500],
                metadatas=metas[i : i + 500],
            )

        logger.info("Ingested %s — %d chunks", pdf_path.name, len(ids))
        return {
            "status": "success",
            "message": f"Ingested {pdf_path.name}",
            "chunks_added": len(ids),
            "total_chunks": self.collection.count(),
        }

    def stats(self) -> dict:
        """Return knowledge-base statistics."""
        n = self.collection.count()
        if n == 0:
            return {"total_chunks": 0, "documents": [], "document_count": 0}

        meta = self.collection.get(limit=n, include=["metadatas"])
        files = sorted({m["source"] for m in meta["metadatas"]})
        return {
            "total_chunks": n,
            "document_count": len(files),
            "documents": files,
        }


# ═══════════════════════════════════════════════════════════════
#  Reranker
# ═══════════════════════════════════════════════════════════════

class Reranker:
    """Cross-encoder reranker for improving retrieval precision."""

    def __init__(self):
        self.model = CrossEncoder(RERANK_MODEL, device="cpu")
        logger.info("Reranker loaded — model=%s", RERANK_MODEL)

    def rerank(self, query: str, hits: list[dict], top_n: int = RERANK_TOP_N) -> list[dict]:
        if not hits:
            return hits

        pairs = [[query, h["text"]] for h in hits]
        scores = self.model.predict(pairs)

        for h, s in zip(hits, scores):
            h["rerank_score"] = float(s)

        hits.sort(key=lambda x: x["rerank_score"], reverse=True)
        return hits[:top_n]


# ═══════════════════════════════════════════════════════════════
#  RAG Pipeline
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
You are an expert Indian Law assistant.

STRICT RULES:

1. Use ONLY the retrieved legal context.
2. Do NOT use prior legal knowledge.
3. Do NOT infer missing articles, sections, or provisions.
4. If the answer is not completely supported by the retrieved context,
   explicitly state:
   "The retrieved documents do not contain sufficient information."
5. Cite the source document whenever making a legal statement.
6. Never invent citations.
7. Format your response in clear markdown with headings and bullet points where appropriate.

End every answer with:

> ⚖️ *This is informational only, not legal advice.*
"""


def _build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    if not hits:
        return "No relevant documents found."

    blocks = []
    for i, h in enumerate(hits, start=1):
        header = (
            f"[Source {i}] "
            f"Act={h.get('act_name')} | "
            f"Part={h.get('part')} | "
            f"Article={h.get('article')} | "
            f"Section={h.get('section')} | "
            f"Page={h.get('page')}"
        )
        blocks.append(header + "\n" + h["text"])
    return "\n\n---\n\n".join(blocks)


class RAGPipeline:
    """End-to-end RAG: retrieve → rerank → generate."""

    def __init__(self, vector_store: VectorStore, reranker: Reranker):
        self.vs = vector_store
        self.reranker = reranker
        self.groq_client = Groq(api_key=GROQ_API_KEY.strip()) if GROQ_API_KEY else None
        logger.info("RAG pipeline ready — Groq model=%s", GROQ_MODEL)

    def ask(self, question: str) -> dict:
        """Answer a legal question using RAG."""
        # 1. Retrieve
        hits = self.vs.retrieve(question, top_k=TOP_K)

        # 2. Rerank
        reranked = self.reranker.rerank(question, hits, top_n=RERANK_TOP_N)

        # 3. Build context
        context = _build_context(reranked)

        # 4. Generate via Groq
        if not self.groq_client:
            return {
                "answer": "⚠️ Groq API key not configured. Please set GROQ_API_KEY in the .env file.",
                "sources": reranked,
            }

        response = self.groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )

        answer = response.choices[0].message.content

        # Build source list for the frontend
        sources = []
        for h in reranked:
            sources.append({
                "act_name": h.get("act_name", "Unknown"),
                "part": h.get("part"),
                "chapter": h.get("chapter"),
                "article": h.get("article"),
                "section": h.get("section"),
                "page": h.get("page"),
                "score": h.get("rerank_score", h.get("score", 0)),
                "excerpt": h["text"][:200] + "…" if len(h["text"]) > 200 else h["text"],
            })

        return {"answer": answer, "sources": sources}
