from __future__ import annotations
from typing import Optional, List, Dict, Any
from pathlib import Path

from .config import Settings

class LLMClient:
    def __init__(self, settings: Settings, system_prompt_path: Path, user_template_path: Path):
        self.settings = settings
        self.system = system_prompt_path.read_text(encoding="utf-8")
        self.user_template = user_template_path.read_text(encoding="utf-8")

    def available(self) -> bool:
        if self.settings.llm_provider.lower() == "openai":
            return bool(self.settings.openai_api_key)
        return False

    def generate(self, question: str, evidence: str) -> str:
        provider = self.settings.llm_provider.lower()
        if provider == "openai":
            return self._openai(question, evidence)
        raise ValueError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")

    def _openai(self, question: str, evidence: str) -> str:
        from openai import OpenAI  # optional dependency
        client = OpenAI(api_key=self.settings.openai_api_key)

        user = self.user_template.format(question=question, evidence=evidence)

        resp = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

def extractive_fallback(question: str, hits: List[Dict[str, Any]]) -> str:
    """No-LLM fallback: returns a concise extract from top evidence."""
    if not hits:
        return "I don’t have that information in my knowledge base."
    top = hits[0]
    snippet = (top.get("text") or "").strip()
    snippet = snippet[:800]
    title = (top.get("metadata") or {}).get("title") or "Source"
    return f"Based on my knowledge base ({title}), here’s what I found:\n\n{snippet}\n\nIf you want, tell me which part you need and I’ll narrow it down."
