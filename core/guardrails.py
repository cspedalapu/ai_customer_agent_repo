from typing import Dict, Any, List, Tuple
from .config import Settings

def enough_evidence(settings: Settings, hits: List[Dict[str, Any]]) -> Tuple[bool, float]:
    """Return (ok, best_similarity)."""
    if not hits:
        return (False, 0.0)
    best = float(hits[0].get("similarity", 0.0))
    return (best >= settings.min_similarity, best)
