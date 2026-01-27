# Knowledge Base Layout

- `sources/` : raw authoritative sources (md/txt/json). Add more here.
- `extracted/` : normalized extracted docs (auto-generated)
- `index/` : chunk index jsonl (auto-generated)
- `vector_store_chroma/` : Chroma persistent vector store (auto-generated)

Tip: For best answers, prefer adding **content-bearing** `.md` or `.txt` docs.
JSON is supported (content/text/notes fields), but metadata-only JSON will produce weak answers.
