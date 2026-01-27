import os
from dataclasses import dataclass

def _env(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return v if v is not None and v != "" else default

def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default

def _env_float(key: str, default: float) -> float:
    try:
        return float(_env(key, str(default)))
    except ValueError:
        return default

@dataclass(frozen=True)
class Settings:
    # Providers
    llm_provider: str = _env("LLM_PROVIDER", "openai")
    llm_model: str = _env("LLM_MODEL", "gpt-4o-mini")
    openai_api_key: str = _env("OPENAI_API_KEY", "")

    embedding_provider: str = _env("EMBEDDING_PROVIDER", "sentence_transformers")
    st_model: str = _env("ST_MODEL", "BAAI/bge-m3")
    openai_embed_model: str = _env("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    # Paths
    kb_path: str = _env("KB_PATH", "knowledge_base")
    chroma_path: str = _env("CHROMA_PATH", "knowledge_base/vector_store_chroma")
    collection_name: str = _env("COLLECTION_NAME", "kb")

    # Retrieval / guardrails
    top_k: int = _env_int("TOP_K", 6)
    min_similarity: float = _env_float("MIN_SIMILARITY", 0.35)
    max_context_chars: int = _env_int("MAX_CONTEXT_CHARS", 8000)

    # Server
    host: str = _env("HOST", "0.0.0.0")
    port: int = _env_int("PORT", 8000)

def get_settings() -> Settings:
    return Settings()
