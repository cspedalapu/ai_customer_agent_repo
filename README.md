# AI Customer Agent (Grounded to Knowledge Base)

This repo is a **from-scratch** template for a realistic customer agent that:
- Retrieves answers only from `knowledge_base/`
- Refuses if the KB doesn't support the answer ("I don’t have that information in my knowledge base.")
- Optionally uses an LLM for natural responses (OpenAI).

Included starter KB files (Texas DPS) are already placed under `knowledge_base/sources/`.

## Repo layout
```
apps/
  api/            # FastAPI: /chat, /ingest
  dashboard/      # Streamlit UI
core/             # extraction, chunking, chroma, retrieval, guardrails, agent
knowledge_base/
  sources/        # put your KB files here
  extracted/      # auto-generated
  index/          # auto-generated
  vector_store_chroma/ # auto-generated
prompts/          # grounding prompts
scripts/          # run helpers
```

## Quickstart (Windows / Mac / Linux)
1) Create venv and install deps:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

2) Configure env:
```bash
cp .env.example .env
# Add OPENAI_API_KEY if you want natural agent responses
```

3) Build the KB index:
```bash
python scripts/ingest_kb.py
```

4) Run API:
```bash
python scripts/run_api.py
```

5) Run dashboard:
```bash
streamlit run apps/dashboard/app.py
```

## API usage
- POST `/ingest` → rebuild index
- POST `/chat` with `{ "message": "..." }`

## Guardrail tuning
- `MIN_SIMILARITY` controls when the agent refuses.
  - If the agent refuses too often, lower it (e.g., 0.28).
  - If the agent hallucinates or answers off-topic, increase it (e.g., 0.45).

## Next improvements (recommended)
- Add a reranker for higher precision (bge-reranker / cross-encoder)
- Add structured tools for forms, locations, and service-specific flows
- Add conversation memory + call notes persistence
- Add voice gateway (Twilio) once chat quality is solid
