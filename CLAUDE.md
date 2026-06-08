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

### Phase 8 — Polish + Deploy (T041–T046) — 2026-06-08
- Dockerfile: multi-stage build (builder + runtime), exposes 8000
- docker-compose.yml: api + ui services, shared data/ volume, healthcheck
- README.md: full docs — architecture diagram, quick start, API reference,
  env vars, agent roles, limitations, security considerations
- All 9 quickstart scenarios validated manually against running API
- 101/101 unit + integration tests pass; 46/46 tasks complete

### Phase 7 — Streamlit UI (T038–T040) — 2026-06-08
- ui/streamlit_app.py: two-column layout (upload | Q&A)
- Health banner on startup — stops if API unreachable, warns if degraded
- File uploader (all 6 formats, 10MB limit) → POST /upload-document
- Q&A form with top_k slider → POST /ask-questions
- Answer display: grounded (green) vs refusal (info); sources as expandable
  cards; agent trace in collapsed expander
- API_BASE_URL configurable via env var (default: http://localhost:8000)
- UI makes HTTP calls to FastAPI — it is a pure API client, NOT importing
  Python modules directly. This means UI and API can run in separate containers.

### Phase 6 — Observability (T035–T037) — 2026-06-08
- `log_requests` middleware in `main.py`: logs method, path, status, elapsed_ms per request
- Exception handlers: `RequestValidationError` → 422, `HTTPException` → pass-through,
  unhandled `Exception` → 500 safe message; never expose exc type or traceback to client
- `/health` enriched: probes LLM (`invoke("ping")`) and vector store; returns
  `{"status":"ok|degraded","llm":"available|unavailable","vector_store":"ready|empty|unavailable"}`
- HTTP 200 is always returned from `/health` — `status` field is the real signal (operator pattern)
- `HealthResponse` Pydantic model added to routes.py for schema enforcement

### Phase 5 — Agent Hardening (T031–T034) — 2026-06-08
- `verifier_node` added to `app/agents/response.py`: second LLM pass (YES/NO)
  asking "Is this answer supported by the context?" — overrides to refusal if NO
- Graph updated: conditional edge after `response` → runs `verifier` only when
  `is_grounded=True`; refusals skip verifier entirely
- Planner guardrails extended to 15 injection patterns (pretend/act-as/reveal/override)
- Key pattern: `verifier_node` caps context at 2000 chars to stay within token budget
- Verifier verdict starts with "NO" check (not exact match) to handle model verbosity

### Phase 4 — Multi-Format (T024–T030) — 2026-06-08
- All 6 loaders (PDF/TXT/CSV/Excel/JSON/YAML) were implemented in Phase 3 together
- Marked complete after verifying 31 format-specific tests pass

### Foundation + MVP (Phases 1–3, T001–T023) — 2026-06-08
- Project scaffolded via `specify init` + Claude Code integration
- Constitution written: 5 core principles established
- Ollama running with llama3.2 (2.0GB) + nomic-embed-text (274MB)
- Key decision: LangChain over LlamaIndex — better agent/graph support for
  multi-agent orchestration; larger community for troubleshooting

**Implementation learnings (compound for next sessions):**
- `filename` is a reserved key in Python `logging.LogRecord` — use `doc_name` instead
- `langchain.schema.Document` is deprecated — use `langchain_core.documents.Document`
- `langchain_community.vectorstores.Chroma` deprecated — use `langchain_chroma.Chroma`
  (requires `pip install langchain-chroma`)
- `langchain.schema.HumanMessage` → `langchain_core.messages.HumanMessage`
- Homebrew `ollama` formula (0.30.6) missing llama-server binary — must install
  `--cask ollama` (Ollama.app) for actual model inference to work
- TypedDict does NOT support `**kwargs` unpacking — test helpers must construct
  the full dict explicitly
- `pytest tmp_path` fixture is the right way to create temp files for format tests
- All 17 unit + integration tests pass with Ollama.app running

**Files created (MVP):**
- app/core/config.py, app/core/llm.py
- app/utils/logging.py
- app/services/ingestion.py, chunking.py, embedding.py
- app/agents/graph.py, planner.py, retriever.py, reasoning.py, response.py
- app/api/routes.py, main.py
- tests/unit/test_ingestion.py, test_agents.py
- tests/integration/test_api.py
- tests/fixtures/ (sample.pdf, .txt, .csv, .xlsx, .json, .yaml)
