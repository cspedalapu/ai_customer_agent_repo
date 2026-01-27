from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import time

from dotenv import load_dotenv
load_dotenv()

from core.config import get_settings
from core.vectorstore import ChromaKB
from core.agent import answer_question
from core.pipeline import ingest

from core.logger import ensure_session_id, log_chat_event

from core.session_store import get_session, update_session
from core.name_parser import extract_name



app = FastAPI(title="AI Customer Agent API", version="0.1.0")
settings = get_settings()
kb = ChromaKB(settings)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest_endpoint():
    result = ingest(settings)
    return {"status": "ok", "result": result}

@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    session_id = ensure_session_id(req.session_id)
    msg = (req.message or "").strip()

    s = get_session(session_id)

    def greet_ask_name():
        return (
            "Hi! Welcome to the Texas Department of Public Safety virtual assistant. "
            "I can answer questions using our knowledge base (driver license, state ID, appointments, and related help).\n\n"
            "May I know your name?"
        )

    # 1) New session → greet and ask name (even if user asked a question)
    if s.stage == "new":
        update_session(session_id, stage="awaiting_name")
        out = {
            "answer": greet_ask_name(),
            "refusal": False,
            "session_id": session_id,
            "stage": "awaiting_name",
        }
        log_chat_event({"session_id": session_id, "stage": "awaiting_name", "question": msg, "answer": out["answer"]})
        return out

    # 2) Awaiting name → try to extract and store it
    if s.stage == "awaiting_name" and not s.name:
        name = extract_name(msg)
        if not name:
            out = {
                "answer": "Sorry — I didn’t catch your name. What should I call you?",
                "refusal": False,
                "session_id": session_id,
                "stage": "awaiting_name",
            }
            log_chat_event({"session_id": session_id, "stage": "awaiting_name", "question": msg, "answer": out["answer"]})
            return out

        update_session(session_id, name=name, stage="active")
        out = {
            "answer": f"Thanks, {name}. How can I help you today?",
            "refusal": False,
            "session_id": session_id,
            "stage": "active",
            "name": name,
        }
        log_chat_event({"session_id": session_id, "stage": "active", "name": name, "question": msg, "answer": out["answer"]})
        return out

    # 3) Active session → answer normally, but personalize
    # (Allow user to update name mid-call)
    maybe_name = extract_name(msg)
    if maybe_name:
        update_session(session_id, name=maybe_name)

    s = get_session(session_id)  # refresh
    out = answer_question(settings, kb, msg)

    if s.name:
        if out.get("refusal"):
            out["answer"] = f"Sorry, {s.name} — {out['answer']}"
        else:
            out["answer"] = f"{s.name}, {out['answer']}"

    out["session_id"] = session_id
    out["stage"] = s.stage
    if s.name:
        out["name"] = s.name

    log_chat_event({
        "session_id": session_id,
        "stage": s.stage,
        "name": s.name,
        "question": msg,
        "answer": out.get("answer"),
        "refusal": out.get("refusal"),
        "best_similarity": out.get("best_similarity"),
        "sources": out.get("sources"),
    })
    return out

@app.post("/retrieve")
def retrieve_debug(req: ChatRequest):
    from core.retriever import retrieve
    hits = retrieve(settings, kb, req.message)
    # return top 5 with small preview
    out = []
    for h in hits[:5]:
        text = (h.get("text") or "")[:400]
        out.append({
            "similarity": h.get("similarity"),
            "distance": h.get("distance"),
            "title": (h.get("metadata") or {}).get("title"),
            "doc_id": (h.get("metadata") or {}).get("doc_id"),
            "preview": text
        })
    return {"hits": out}

@app.get("/history/{session_id}")
def history(session_id: str, limit: int = 50):
    import json
    from pathlib import Path

    path = Path("data/conversations.jsonl")
    if not path.exists():
        return {"events": []}

    events = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("session_id") == session_id:
                    events.append(obj)
            except Exception:
                continue

    return {"events": events[-limit:]}
