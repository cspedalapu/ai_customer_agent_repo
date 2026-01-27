from __future__ import annotations
from typing import Dict, Any, List
from sentence_transformers import CrossEncoder

_RERANKER = None

def get_reranker(model_name: str) -> CrossEncoder:
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(model_name)
    return _RERANKER

def rerank_hits(query: str, hits: List[Dict[str, Any]], model_name: str, keep_k: int, max_doc_chars: int) -> List[Dict[str, Any]]:
    if not hits:
        return hits

    ce = get_reranker(model_name)

    pairs = []
    for h in hits:
        txt = (h.get("text") or "").strip()
        txt = txt[:max_doc_chars]
        pairs.append((query, txt))

    scores = ce.predict(pairs)  # higher is better

    out = []
    for h, s in zip(hits, scores):
        hh = dict(h)
        hh["rerank_score"] = float(s)
        out.append(hh)

    out.sort(key=lambda x: x.get("rerank_score", -1e9), reverse=True)
    return out[:keep_k]
