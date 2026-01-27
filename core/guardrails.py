import re
from typing import Dict, Any, List, Tuple
from .config import Settings

_WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

def _tokens(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())

def keyword_overlap_ratio(question: str, text: str) -> float:
    # ratio = |Q ∩ T| / |Q|
    q = set(_tokens(question))
    if not q:
        return 0.0
    t = set(_tokens(text))
    return len(q.intersection(t)) / max(1, len(q))

def enough_evidence(settings: Settings, question: str, hits: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    if not hits:
        return (False, {"best_similarity": 0.0, "keyword_overlap": 0.0})

    best = float(hits[0].get("similarity", 0.0))
    top_text = hits[0].get("text") or ""
    overlap = keyword_overlap_ratio(question, top_text)

    ok = (best >= settings.high_similarity_override) or (
        best >= settings.min_similarity and overlap >= settings.min_keyword_overlap
    )

    return (ok, {
        "best_similarity": best,
        "keyword_overlap": overlap,
        "min_similarity": settings.min_similarity,
        "min_keyword_overlap": settings.min_keyword_overlap,
        "high_similarity_override": settings.high_similarity_override,
    })
