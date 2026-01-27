from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import chromadb
from chromadb.utils import embedding_functions

from .config import Settings

def _build_embedding_fn(settings: Settings):
    provider = settings.embedding_provider.lower().strip()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for EMBEDDING_PROVIDER=openai")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.openai_embed_model,
        )
    # default: sentence-transformers
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.st_model
    )

class ChromaKB:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.embed_fn = _build_embedding_fn(settings)
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=self.embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_text: str, top_k: int) -> Dict[str, Any]:
        return self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

def distance_to_similarity(d: float) -> float:
    """Best-effort normalization for Chroma distances.
    - For cosine distance (0..2): similarity ≈ 1 - d
    - Otherwise: similarity = 1/(1+d)
    """
    try:
        d = float(d)
    except Exception:
        return 0.0
    if 0.0 <= d <= 2.0:
        return max(0.0, 1.0 - d)
    return 1.0 / (1.0 + max(d, 0.0))
