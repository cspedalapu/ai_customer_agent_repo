from __future__ import annotations
from typing import Any, Dict, List, Tuple

from .config import Settings
from .vectorstore import ChromaKB, distance_to_similarity

def retrieve(settings: Settings, kb: ChromaKB, question: str, top_k: int | None = None) -> List[Dict[str, Any]]:
    k = top_k if top_k is not None else settings.top_k
    res = kb.query(question, top_k=k)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    items: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        sim = distance_to_similarity(dist)
        items.append({
            "text": doc,
            "metadata": meta or {},
            "distance": dist,
            "similarity": sim,
        })
    items.sort(key=lambda x: x["similarity"], reverse=True)
    return items
