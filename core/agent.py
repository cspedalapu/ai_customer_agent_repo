from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path

from .config import Settings
from .retriever import retrieve
from .guardrails import enough_evidence
from .llm import LLMClient, extractive_fallback

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
    hits = retrieve(settings, kb, question)
    ok, best = enough_evidence(settings, hits)

    if not ok:
        return {
            "answer": "I don’t have that information in my knowledge base.",
            "refusal": True,
            "best_similarity": best,
            "sources": _format_sources(hits),
        }

    evidence = _format_evidence(hits, max_chars=settings.max_context_chars)

    llm = LLMClient(
        settings=settings,
        system_prompt_path=Path("prompts/system.txt"),
        user_template_path=Path("prompts/user_template.txt"),
    )

    if llm.available():
        ans = llm.generate(question=question, evidence=evidence)
    else:
        ans = extractive_fallback(question, hits)

    return {
        "answer": ans,
        "refusal": False,
        "best_similarity": best,
        "sources": _format_sources(hits),
    }
