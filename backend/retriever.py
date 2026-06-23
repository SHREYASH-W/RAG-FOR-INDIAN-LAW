"""
Retriever — hybrid search (dense + BM25), query expansion,
reciprocal rank fusion, and contextual compression.
"""

import re
import logging
import math
from collections import defaultdict

from rank_bm25 import BM25Okapi
from groq import Groq

from config import (
    TOP_K, RERANK_TOP_N, GROQ_API_KEY, GROQ_MODEL,
    QUERY_EXPANSION_ENABLED, QUERY_EXPANSION_COUNT,
    COMPRESSION_ENABLED, BM25_WEIGHT, DENSE_WEIGHT,
)
from prompts import QUERY_EXPANSION_PROMPT, COMPRESSION_PROMPT

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  BM25 Sparse Index
# ═══════════════════════════════════════════════════════════════

def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercasing tokenizer for BM25."""
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


class BM25Index:
    """Wrapper around BM25Okapi that maps corpus indices to chunk IDs."""

    def __init__(self):
        self.corpus_tokens: list[list[str]] = []
        self.corpus_docs: list[dict] = []
        self.bm25: BM25Okapi | None = None
        self._built = False

    def build(self, documents: list[dict]):
        """
        Build the BM25 index from a list of chunk dicts.
        Each dict must have 'text' and 'id' keys.
        """
        self.corpus_docs = documents
        self.corpus_tokens = [_tokenize(doc["text"]) for doc in documents]

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
            self._built = True
            logger.info("BM25 index built — %d documents", len(self.corpus_docs))
        else:
            self._built = False

    def search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """Search and return top-K results with BM25 scores."""
        if not self._built or not self.bm25:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices
        scored = list(enumerate(scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        results = []
        for idx, score in top:
            if score <= 0:
                continue
            doc = self.corpus_docs[idx].copy()
            doc["bm25_score"] = float(score)
            results.append(doc)

        return results


# ═══════════════════════════════════════════════════════════════
#  Query Expansion
# ═══════════════════════════════════════════════════════════════

class QueryExpander:
    """Uses LLM to generate alternative search queries."""

    def __init__(self, groq_client: Groq | None):
        self.client = groq_client

    def expand(self, question: str) -> list[str]:
        """
        Generate alternative queries. Returns a list that always
        starts with the original question.
        """
        queries = [question]

        if not QUERY_EXPANSION_ENABLED or not self.client:
            return queries

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{
                    "role": "user",
                    "content": QUERY_EXPANSION_PROMPT.format(question=question),
                }],
                temperature=0.3,
                max_tokens=200,
            )
            raw = response.choices[0].message.content.strip()
            alternatives = [
                line.strip()
                for line in raw.split("\n")
                if line.strip() and len(line.strip()) > 5
            ]
            queries.extend(alternatives[:QUERY_EXPANSION_COUNT])
            logger.info(
                "Query expanded: %s → %d variants",
                question[:50], len(queries),
            )
        except Exception as e:
            logger.warning("Query expansion failed: %s", e)

        return queries


# ═══════════════════════════════════════════════════════════════
#  Reciprocal Rank Fusion
# ═══════════════════════════════════════════════════════════════

def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[dict]:
    """
    Merge multiple ranked result lists using RRF.

    Each result dict must have 'text' to be used as dedup key.
    Returns merged list sorted by RRF score.
    """
    if weights is None:
        weights = [1.0] * len(result_lists)

    # text → aggregated data
    scores: dict[str, float] = defaultdict(float)
    best_doc: dict[str, dict] = {}

    for weight, results in zip(weights, result_lists):
        for rank, doc in enumerate(results, start=1):
            key = doc["text"][:200]  # Dedup by first 200 chars
            rrf_score = weight / (k + rank)
            scores[key] += rrf_score

            # Keep the version with more metadata
            if key not in best_doc or len(doc) > len(best_doc[key]):
                best_doc[key] = doc

    # Sort by RRF score
    sorted_keys = sorted(scores, key=scores.get, reverse=True)

    merged = []
    for key in sorted_keys:
        doc = best_doc[key].copy()
        doc["rrf_score"] = scores[key]
        merged.append(doc)

    return merged


# ═══════════════════════════════════════════════════════════════
#  Contextual Compression
# ═══════════════════════════════════════════════════════════════

class ContextCompressor:
    """Compresses retrieved chunks to only the relevant portions."""

    def __init__(self, groq_client: Groq | None):
        self.client = groq_client

    def compress(self, question: str, chunks: list[dict]) -> list[dict]:
        """
        For each chunk, extract only the relevant sentences.
        Falls back to the full chunk if compression fails.
        """
        if not COMPRESSION_ENABLED or not self.client:
            return chunks

        compressed = []
        for chunk in chunks:
            try:
                response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{
                        "role": "user",
                        "content": COMPRESSION_PROMPT.format(
                            question=question,
                            chunk_text=chunk["text"],
                        ),
                    }],
                    temperature=0.0,
                    max_tokens=500,
                )
                extracted = response.choices[0].message.content.strip()

                # Only use compressed version if it's substantial
                if len(extracted) > 20:
                    c = chunk.copy()
                    c["text"] = extracted
                    compressed.append(c)
                else:
                    compressed.append(chunk)
            except Exception as e:
                logger.warning("Compression failed for chunk: %s", e)
                compressed.append(chunk)

        return compressed


# ═══════════════════════════════════════════════════════════════
#  Hybrid Retriever (Orchestrator)
# ═══════════════════════════════════════════════════════════════

class HybridRetriever:
    """
    Orchestrates the full retrieval pipeline:
    query expansion → dense + sparse search → RRF → rerank → compress
    """

    def __init__(self, vector_store, reranker, groq_client: Groq | None):
        self.vs = vector_store
        self.reranker = reranker
        self.query_expander = QueryExpander(groq_client)
        self.compressor = ContextCompressor(groq_client)
        self.bm25_index = BM25Index()

    def build_bm25_index(self):
        """Build BM25 index from all documents in ChromaDB."""
        count = self.vs.collection.count()
        if count == 0:
            logger.info("No documents in ChromaDB — skipping BM25 build")
            return

        logger.info("Building BM25 index from %d chunks…", count)
        # Fetch all documents in batches
        all_docs = []
        batch_size = 5000
        offset = 0

        while offset < count:
            batch = self.vs.collection.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas"],
            )
            for doc_id, text, meta in zip(
                batch["ids"], batch["documents"], batch["metadatas"]
            ):
                all_docs.append({
                    "id": doc_id,
                    "text": text,
                    **meta,
                })
            offset += batch_size

        self.bm25_index.build(all_docs)

    def retrieve(
        self,
        question: str,
        top_k: int = TOP_K,
        rerank_top_n: int = RERANK_TOP_N,
    ) -> list[dict]:
        """
        Full retrieval pipeline.
        Returns reranked, compressed chunks ready for LLM context.
        """
        # 1. Query expansion
        queries = self.query_expander.expand(question)

        # 2. Dense search (ChromaDB) for each query variant
        dense_results: list[dict] = []
        for q in queries:
            hits = self.vs.retrieve(q, top_k=top_k)
            dense_results.extend(hits)

        # 3. Sparse search (BM25) for each query variant
        sparse_results: list[dict] = []
        for q in queries:
            hits = self.bm25_index.search(q, top_k=top_k)
            sparse_results.extend(hits)

        # 4. Reciprocal Rank Fusion
        if sparse_results:
            merged = reciprocal_rank_fusion(
                [dense_results, sparse_results],
                weights=[DENSE_WEIGHT, BM25_WEIGHT],
            )
        else:
            # Fall back to dense only if BM25 isn't built
            merged = dense_results

        # Deduplicate by text content
        seen = set()
        unique = []
        for doc in merged:
            key = doc["text"][:200]
            if key not in seen:
                seen.add(key)
                unique.append(doc)

        # 5. Cross-encoder reranking on the merged set
        # Take top candidates for reranking (limit to avoid slowness)
        candidates = unique[:top_k * 2]
        reranked = self.reranker.rerank(question, candidates, top_n=rerank_top_n)

        # 6. Contextual compression
        compressed = self.compressor.compress(question, reranked)

        logger.info(
            "Retrieval: %d dense + %d sparse → %d merged → %d reranked → %d final",
            len(dense_results), len(sparse_results),
            len(unique), len(reranked), len(compressed),
        )

        return compressed
