from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path

from .config import Settings
from .retriever import retrieve
from .guardrails import enough_evidence
from .llm import LLMClient, extractive_fallback

from time import perf_counter
from .reranker import rerank_hits

import time
t0 = time.perf_counter()


_LLM_SINGLETON = None

def get_llm(settings: Settings) -> LLMClient:
    global _LLM_SINGLETON
    if _LLM_SINGLETON is None:
        _LLM_SINGLETON = LLMClient(
            settings=settings,
            system_prompt_path=Path("prompts/system.txt"),
            user_template_path=Path("prompts/user_template.txt"),
        )
    return _LLM_SINGLETON


def _format_evidence(hits: List[Dict[str, Any]], max_chars: int) -> str:
    blocks = []
    total = 0
    for i, h in enumerate(hits, start=1):
        meta = h.get("metadata") or {}
        title = meta.get("title") or meta.get("doc_id") or "Untitled"
        url = meta.get("source_url") or meta.get("source") or meta.get("url") or ""
        header = f"[{i}] {title}" + (f" ({url})" if url else "")
        text = (h.get("text") or "").strip()
        block = header + "\n" + text
        if total + len(block) > max_chars:
            remaining = max(0, max_chars - total)
            if remaining > 200:
                blocks.append(block[:remaining])
            break
        blocks.append(block)
        total += len(block) + 2
    return "\n\n".join(blocks)

def _format_sources(hits: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    out = []
    for h in hits[:limit]:
        meta = h.get("metadata") or {}
        out.append({
            "title": meta.get("title") or meta.get("doc_id") or "Source",
            "source_url": meta.get("source_url") or "",
            "doc_id": meta.get("doc_id") or "",
            "similarity": round(float(h.get("similarity", 0.0)), 4),
        })
    return out

def answer_question(settings: Settings, kb, question: str) -> Dict[str, Any]:
    t0 = perf_counter()

    # Stage 1: retrieve MORE candidates (fast)
    hits = retrieve(settings, kb, question, top_k=settings.retrieve_top_n)
    t_retrieve = time.perf_counter()

    t1 = perf_counter()

    # Stage 2: rerank and KEEP only the best few (accurate + small context)
    if settings.use_reranker:
        hits = rerank_hits(
            query=question,
            hits=hits,
            model_name=settings.rerank_model,
            keep_k=settings.rerank_keep_k,
            max_doc_chars=settings.rerank_max_doc_chars,
        )
    else:
        # No reranker: still keep small set
        hits = hits[:settings.top_k]

    t2 = perf_counter()

    ok, best = enough_evidence(settings, hits)

    timings_ms = {
        "retrieve_ms": round((t1 - t0) * 1000, 1),
        "rerank_ms": round((t2 - t1) * 1000, 1),
    }

    best = float(dbg.get("best_similarity", 0.0))


    if not ok:
    # If it's somewhat relevant, ask ONE clarifying question instead of hard refusal
        if best >= settings.clarify_min_similarity:
            return {
                "answer": build_clarifying_question(question),
                "refusal": False,
                "clarification": True,
                "best_similarity": best,
                "sources": _format_sources(hits),
            }

        return {
    "answer": "I don’t have that information in my knowledge base.",
    "refusal": True,
    "best_similarity": best,
    "sources": _format_sources(hits),
    "timings_ms": timings_ms,
}



    evidence = _format_evidence(hits, max_chars=settings.max_context_chars)

    llm = get_llm(settings)
    t_done = time.perf_counter()

    if llm.available():
        t_llm0 = perf_counter()
        ans = llm.generate(question=question, evidence=evidence)
        t_llm1 = perf_counter()
        timings_ms["llm_ms"] = round((t_llm1 - t_llm0) * 1000, 1)
    else:
        ans = extractive_fallback(question, hits)
        timings_ms["llm_ms"] = 0.0

    return {
    "answer": ans,
    "refusal": False,
    "best_similarity": best,
    "sources": _format_sources(hits),
    "timings_ms": timings_ms,
}

def build_clarifying_question(question: str) -> str:
    q = (question or "").lower()

    if "appointment" in q or "schedule" in q or "book" in q:
        return "Sure — is this appointment for a Driver License, a State ID, or something else?"

    if "id" in q and ("state" in q or "identification" in q):
        return "Got it — are you applying for a first-time State ID, or renewing/replacing an existing one?"

    if "license" in q:
        return "Understood — is this for a first-time Driver License, a renewal, or a replacement?"

    return "Just to confirm — what exact service are you trying to complete?"
