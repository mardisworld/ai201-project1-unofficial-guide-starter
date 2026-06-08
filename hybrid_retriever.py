"""
Hybrid retrieval: dense semantic search + BM25 keyword search.

This is an OPTIONAL strategy, selected from the UI. It does not modify the
original semantic pipeline — it reuses retriever.retrieve() unchanged for the
dense half and adds a BM25 keyword index over the same chunk corpus, then fuses
the two rankings with Reciprocal Rank Fusion (RRF).

Why hybrid: dense embeddings capture meaning but can miss chunks that don't
restate their subject; BM25 catches exact-term matches (plan names, dollar
figures, acronyms like "ICR"/"PAYE") that dense search ranks low. RRF combines
both so a chunk that either side ranks highly can surface.
"""

import re

from rank_bm25 import BM25Okapi

from config import N_RESULTS
from retriever import retrieve, get_collection

# Built lazily on first hybrid query so the original semantic path pays no cost.
_bm25 = None
_bm25_chunks = None


def _tokenize(text):
    """Lowercase alphanumeric tokenization for BM25."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _build_index():
    """Load every stored chunk and build a BM25 index over the chunk texts."""
    global _bm25, _bm25_chunks

    data = get_collection().get(include=["documents", "metadatas"])
    documents = data["documents"]
    metadatas = data["metadatas"]

    _bm25_chunks = []
    corpus_tokens = []
    for text, meta in zip(documents, metadatas):
        _bm25_chunks.append({
            "text": text,
            "student_loan_article": meta.get("student_loan_article"),
            "section_header": meta.get("section_header"),
            "chunk_id": meta.get("chunk_id"),
        })
        corpus_tokens.append(_tokenize(text))

    _bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None


def _ensure_index():
    if _bm25 is None or not _bm25_chunks:
        _build_index()


def reset_index():
    """Drop the cached BM25 index (call after re-ingestion)."""
    global _bm25, _bm25_chunks
    _bm25 = None
    _bm25_chunks = None


def _matches_filter(chunk, where):
    """True if the chunk satisfies a simple equality metadata filter."""
    if not where:
        return True
    return all(chunk.get(field) == value for field, value in where.items())


def hybrid_retrieve(query, n_results=N_RESULTS, pool=None, rrf_k=60, where=None):
    """
    Retrieve chunks by fusing dense semantic and BM25 keyword rankings.

    Returns a list of dicts in the same shape as retriever.retrieve(), so it is
    a drop-in replacement for generation. Each result also carries:
      - "rrf_score" : the fused Reciprocal Rank Fusion score
      - "dense_rank"/"bm25_rank" : 1-based rank in each ranker (or None if absent)

    RRF score for a chunk = sum over rankers of 1 / (rrf_k + rank).

    `where` is an optional metadata equality filter (e.g.
    {"student_loan_article": "8. ..."}) applied to both retrievers.
    """
    _ensure_index()
    if not _bm25_chunks:
        return []

    # Pull a wider candidate pool from each ranker than we finally return, so
    # fusion has room to promote a chunk that only one side ranked highly.
    if pool is None:
        pool = max(n_results * 3, 20)

    # --- Dense half: reuse the existing semantic retriever, unchanged. ---
    dense = retrieve(query, n_results=pool, where=where)

    # --- Keyword half: BM25 over the same corpus (filtered to match). ---
    scores = _bm25.get_scores(_tokenize(query))
    top_bm25 = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    bm25 = [
        _bm25_chunks[i]
        for i in top_bm25
        if _matches_filter(_bm25_chunks[i], where)
    ][:pool]

    # --- Reciprocal Rank Fusion, keyed by chunk_id. ---
    fused = {}      # chunk_id -> {"score", "chunk", "dense_rank", "bm25_rank"}

    for rank, chunk in enumerate(dense):
        cid = chunk["chunk_id"]
        entry = fused.setdefault(cid, {"score": 0.0, "chunk": chunk,
                                       "dense_rank": None, "bm25_rank": None})
        entry["score"] += 1.0 / (rrf_k + rank + 1)
        entry["dense_rank"] = rank + 1
        entry["chunk"] = chunk  # prefer the dense dict (has distance/similarity)

    for rank, chunk in enumerate(bm25):
        cid = chunk["chunk_id"]
        entry = fused.setdefault(cid, {"score": 0.0, "chunk": chunk,
                                       "dense_rank": None, "bm25_rank": None})
        entry["score"] += 1.0 / (rrf_k + rank + 1)
        entry["bm25_rank"] = rank + 1

    ranked = sorted(fused.values(), key=lambda e: e["score"], reverse=True)[:n_results]

    results = []
    for entry in ranked:
        chunk = dict(entry["chunk"])
        chunk["rrf_score"] = entry["score"]
        chunk["dense_rank"] = entry["dense_rank"]
        chunk["bm25_rank"] = entry["bm25_rank"]
        # Keep keys consistent with retrieve() for any consumer that expects them.
        chunk.setdefault("distance", None)
        chunk.setdefault("similarity", None)
        results.append(chunk)

    return results
