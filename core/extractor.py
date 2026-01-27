"""Source -> ExtractedDoc

This module intentionally keeps extraction simple:
- .md/.txt: used as-is
- .json: if it contains 'content' or 'text', use it; else fall back to 'notes'
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional
import json

from .utils import read_text, read_json, sha256_text, write_json

@dataclass
class ExtractedDoc:
    doc_id: str
    title: str
    text: str
    metadata: Dict[str, Any]

def _safe_doc_id(path: Path, meta: Dict[str, Any]) -> str:
    # Prefer explicit doc_id from metadata, else filename stem
    return str(meta.get("doc_id") or path.stem)

def extract_one(path: Path) -> ExtractedDoc:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        text = read_text(path).strip()
        meta = {"source_file": path.name, "source_type": suffix.lstrip(".")}
        title = path.stem
    elif suffix == ".json":
        meta = read_json(path)
        title = str(meta.get("title") or path.stem)
        # Try a few fields for usable content
        text = str(meta.get("content") or meta.get("text") or meta.get("notes") or "").strip()
        if not text:
            # Very strict: if no content, keep minimal placeholder so pipeline doesn't crash
            text = f"Metadata-only document. Title: {title}. Source URL: {meta.get('source_url','')}."
            meta["metadata_only"] = True
    else:
        raise ValueError(f"Unsupported file type: {path.name}")

    doc_id = _safe_doc_id(path, meta)
    meta = dict(meta)
    meta.setdefault("title", title)
    meta.setdefault("doc_id", doc_id)
    meta.setdefault("source_file", path.name)
    meta["text_hash"] = sha256_text(text)
    return ExtractedDoc(doc_id=doc_id, title=title, text=text, metadata=meta)

def extract_all(sources_dir: Path, extracted_dir: Path) -> int:
    extracted_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in sorted(sources_dir.rglob("*")):
        if p.is_dir():
            continue
        if p.suffix.lower() not in {".md", ".txt", ".json"}:
            continue
        doc = extract_one(p)
        out = extracted_dir / f"{doc.doc_id}.json"
        write_json(out, {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "text": doc.text,
            "metadata": doc.metadata,
        })
        count += 1
    return count
