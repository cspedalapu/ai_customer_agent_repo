from __future__ import annotations
import re
from typing import Optional

# Handles: "my name is John", "I'm John", "I am John", "this is John"
_PATTERNS = [
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z\s.'-]{0,40})\b", re.IGNORECASE),
    re.compile(r"\bi am\s+([A-Za-z][A-Za-z\s.'-]{0,40})\b", re.IGNORECASE),
    re.compile(r"\bi'm\s+([A-Za-z][A-Za-z\s.'-]{0,40})\b", re.IGNORECASE),
    re.compile(r"\bthis is\s+([A-Za-z][A-Za-z\s.'-]{0,40})\b", re.IGNORECASE),
]

def extract_name(text: str) -> Optional[str]:
    if not text:
        return None

    t = text.strip()
    for p in _PATTERNS:
        m = p.search(t)
        if m:
            name = m.group(1).strip()
            return _clean(name)

    # If user just replies with a short name (1–3 tokens), treat it as name
    # Example: "Chandra", "Appala Naidu"
    tokens = re.findall(r"[A-Za-z][A-Za-z.'-]*", t)
    if 1 <= len(tokens) <= 3 and len(t) <= 30:
        return _clean(" ".join(tokens))

    return None

def _clean(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    # Prevent weird all-caps shouting
    if len(name) >= 2 and name.isupper():
        name = name.title()
    return name[:50]
