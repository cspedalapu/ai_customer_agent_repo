from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
    """Simple character chunker with overlap."""
    if not text:
        return []
    text = text.replace("\r\n", "\n")
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks

def make_chunks(doc_id: str, title: str, text: str, metadata: Dict[str, Any],
                chunk_size: int = 900, overlap: int = 120) -> List[Chunk]:
    out: List[Chunk] = []
    parts = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    for i, part in enumerate(parts):
        cid = f"{doc_id}::chunk{i:04d}"
        md = dict(metadata)
        md.update({
            "doc_id": doc_id,
            "title": title,
            "chunk_index": i,
        })
        out.append(Chunk(chunk_id=cid, text=part, metadata=md))
    return out
