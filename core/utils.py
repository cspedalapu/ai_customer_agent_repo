import hashlib
import json
from pathlib import Path
from typing import Any, Dict

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def read_text(path: Path) -> str:
    """
    Robust text reader for mixed-encoding corpora.
    Tries common encodings in order.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    data = path.read_bytes()
    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    # last resort
    return data.decode("utf-8", errors="ignore")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(read_text(path))

def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
