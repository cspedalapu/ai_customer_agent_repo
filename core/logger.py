# core/logger.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json
import time
import uuid

LOG_PATH = Path("data/conversations.jsonl")

def ensure_session_id(session_id: str | None) -> str:
    return session_id.strip() if session_id and session_id.strip() else str(uuid.uuid4())

def log_chat_event(event: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = dict(event)
    event.setdefault("ts", time.time())
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
