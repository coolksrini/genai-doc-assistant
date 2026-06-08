<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan at
specs/001-genai-document-qa/plan.md
<!-- SPECKIT END -->

# genai-doc-assistant — Development Guide

> This file is the **living brain** of the project (Compound Engineering).
> It grows after each task. Always read this before starting any work.
> For non-negotiable principles, see `.specify/memory/constitution.md`.

## What This Project Is

A Generative AI-powered document Q&A system for the Edureka GenAI & ML Capstone.
Users upload enterprise documents (PDF, TXT, CSV, Excel, JSON, YAML) and ask
natural language questions. Autonomous AI agents retrieve relevant context and
generate grounded answers using RAG.

**Capstone course**: Edureka PGP GenAI & ML — Batch B9
**Submission deadline**: 30 June 2026
**Submission**: zip file (code mandatory; docs + execution results good-to-have)

## Stack at a Glance

| Layer | Technology |
|---|---|
| Agent framework | LangChain + LangGraph |
| LLM (dev) | Ollama — llama3.2 (`http://localhost:11434/v1`) |
| LLM (prod) | Any OpenAI-compatible — change `LLM_BASE_URL` + `LLM_API_KEY` env vars |
| Embeddings | nomic-embed-text via Ollama |
| Vector DB | ChromaDB |
| API | FastAPI |
| UI | Streamlit |
| Deployment | Docker / Render |

## Folder Structure

```
genai-doc-assistant/
  app/
    api/          ← FastAPI routes
    services/     ← document ingestion, chunking, embedding
    agents/       ← Planner, Retriever, Reasoning, Response agents
    core/         ← config, LLM setup, vector store client
    utils/        ← helpers, logging
  data/           ← uploaded files (gitignored)
  .specify/       ← Spec Kit project structure
  main.py         ← FastAPI app entry point
  requirements.txt
  .gitignore
  CLAUDE.md       ← this file
```

## Key Constraints (from Constitution)

1. LLM answers ONLY from retrieved document context — never from training data
2. Four agents: Planner → Retriever → Reasoning → Response (via LangGraph)
3. Format parsing isolated to `app/services/` — agents never touch file I/O
4. Swap LLM/embeddings via env vars only — zero code changes needed
5. All inputs validated at API boundary (whitelist: pdf/txt/csv/xlsx/json/yaml, max 10MB)

## Environment Variables

```bash
LLM_BASE_URL=http://localhost:11434/v1   # Ollama local (dev)
LLM_API_KEY=ollama                        # placeholder for Ollama
LLM_MODEL=llama3.2
EMBED_MODEL=nomic-embed-text
CHROMA_PATH=./data/chroma_db
MAX_FILE_SIZE_MB=10
CHUNK_SIZE=200
CHUNK_OVERLAP=20
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check → 200 OK |
| POST | `/upload-document` | Upload + ingest a document |
| POST | `/ask-questions` | Ask a question against ingested docs |

## Compound Engineering Log

> Each completed task adds an entry here with key learnings.

### Foundation (Task 1) — 2026-06-08
- Project scaffolded via `specify init` + Claude Code integration
- Constitution written: 5 core principles established
- Ollama running with llama3.2 (2.0GB) + nomic-embed-text (274MB)
- Key decision: LangChain over LlamaIndex — better agent/graph support for
  multi-agent orchestration; larger community for troubleshooting
