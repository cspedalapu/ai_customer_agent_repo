# Architecture

## Goal
A grounded customer agent that answers **only** from `knowledge_base/`.

## Pipeline
1. Sources (`knowledge_base/sources`) → extract text (`knowledge_base/extracted`)
2. Chunk + index (`knowledge_base/index/chunks.jsonl`)
3. Embed + store in Chroma (`knowledge_base/vector_store_chroma`)
4. Retrieval + relevance gate (MIN_SIMILARITY)
5. Answer generation (OpenAI optional) **only using evidence**

## Key guardrail
If evidence is weak or irrelevant, the agent returns:
“I don’t have that information in my knowledge base.”
