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
    out = answer_question(settings, kb, req.message)
    return out
