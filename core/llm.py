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
            return bool(self.settings.openai_api_key or self.settings.github_token)
        return False

    def generate(self, question: str, evidence: str) -> str:
        provider = self.settings.llm_provider.lower()
        if provider == "openai":
            return self._openai(question, evidence)
        if provider == "github_models":
            return self._github_models(question, evidence)
        raise ValueError(f"Unsupported LLM_PROVIDER: {self.settings.llm_provider}")


    def _openai(self, question: str, evidence: str) -> str:
        from openai import OpenAI  # optional dependency

        base_url = (self.settings.openai_base_url or "").rstrip("/") or None

        # Use OPENAI_API_KEY if present; otherwise fall back to GITHUB_TOKEN
        api_key = self.settings.openai_api_key or self.settings.github_token
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY (or GITHUB_TOKEN for GitHub Models).")

        default_headers = None
        if base_url and "models.github.ai" in base_url:
            # GitHub Models expects these headers (see GitHub Models quickstart)
            default_headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": self.settings.github_api_version,
            }

        client = OpenAI(api_key=api_key, base_url=base_url, default_headers=default_headers)

        user = self.user_template.format(question=question, evidence=evidence)

        resp = client.chat.completions.create(
    model=self.settings.llm_model,
    messages=[
        {"role": "system", "content": self.system},
        {"role": "user", "content": user},
    ],
    temperature=self.settings.llm_temperature,
    max_tokens=self.settings.llm_max_tokens,
)

        return resp.choices[0].message.content.strip()

    

    def _github_models(self, question: str, evidence: str) -> str:
        from openai import OpenAI

        client = OpenAI(
            base_url=self.settings.github_models_endpoint.rstrip("/"),
            api_key=self.settings.github_token,
            default_headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": self.settings.github_api_version,
            },
        )

        user = self.user_template.format(question=question, evidence=evidence)

        resp = client.chat.completions.create(
            model=self.settings.llm_model,  # e.g., "openai/gpt-4o"
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
