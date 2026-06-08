# Implementation Plan: GenAI Document Q&A System

**Branch**: `001-genai-document-qa` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

## Summary

Build a four-agent RAG pipeline that lets users upload enterprise documents
(PDF, TXT, CSV, Excel, JSON, YAML), store them as vector embeddings in ChromaDB,
and ask natural language questions answered exclusively from retrieved document
context. The system exposes a FastAPI REST backend and an optional Streamlit UI,
runs fully offline with Ollama (llama3.2 + nomic-embed-text), and swaps to any
OpenAI-compatible cloud provider via environment variables.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**:
- `langchain`, `langchain-community`, `langgraph` — agent orchestration & RAG chain
- `langchain-ollama` — Ollama LLM + embedding integration
- `chromadb` — local vector store
- `fastapi`, `uvicorn` — REST API
- `streamlit` — web UI
- `pypdf2` — PDF parsing
- `pandas`, `openpyxl` — CSV / Excel parsing
- `pyyaml` — YAML parsing
- `python-multipart` — FastAPI file uploads
- `pytest`, `httpx` — testing

**Storage**: ChromaDB on local disk (`./data/chroma_db`); interface abstracted
for Pinecone/FAISS swap.

**Testing**: pytest + httpx (async FastAPI client)

**Target Platform**: macOS/Linux local (dev); Docker container (prod)

**Project Type**: Web service (FastAPI backend) + UI (Streamlit)

**Performance Goals**: Answer latency < 30s on local Ollama hardware (llama3.2 3B)

**Constraints**: Max file size 10MB; offline-capable in dev; zero hardcoded model
names or API keys.

**Scale/Scope**: Single user / small team demo; no concurrent user requirement.

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Grounded Responses Only | PASS | RAG chain instructs LLM to use only context; refusal on no-match |
| II. Modular Agent Architecture | PASS | LangGraph graph with 4 named nodes; each independently testable |
| III. Format-Agnostic Ingestion | PASS | Format loaders isolated to app/services/ingestion.py |
| IV. Local-First, Cloud-Swap-Ready | PASS | All model refs via env vars; Ollama default |
| V. Safety & Validation at Every Boundary | PASS | FastAPI middleware validates type/size; output verification node |

No violations. All gates pass.

## Project Structure

### Documentation (this feature)

```
specs/001-genai-document-qa/
├── plan.md           <- this file
├── research.md       <- Phase 0: technology decisions
├── data-model.md     <- Phase 1: entities & data flow
├── quickstart.md     <- Phase 1: validation guide
├── contracts/
│   └── api.md        <- Phase 1: API endpoint contracts
└── tasks.md          <- Phase 2: /speckit-tasks output
```

### Source Code

```
genai-doc-assistant/
├── app/
│   ├── api/
│   │   └── routes.py         <- FastAPI routes (upload, ask, health)
│   ├── agents/
│   │   ├── graph.py          <- LangGraph StateGraph definition
│   │   ├── planner.py        <- Planner agent node
│   │   ├── retriever.py      <- Retriever agent node
│   │   ├── reasoning.py      <- Reasoning agent node
│   │   └── response.py       <- Response agent node
│   ├── services/
│   │   ├── ingestion.py      <- document loading & format dispatch
│   │   ├── chunking.py       <- text chunking (200 tokens + overlap)
│   │   └── embedding.py      <- embedding + ChromaDB store/retrieve
│   ├── core/
│   │   ├── config.py         <- env var loading (pydantic Settings)
│   │   └── llm.py            <- LLM + embedding model factory
│   └── utils/
│       └── logging.py        <- structured JSON logger
├── data/                     <- uploaded files + chroma_db (gitignored)
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   ├── test_chunking.py
│   │   ├── test_agents.py
│   │   └── test_embedding.py
│   └── integration/
│       └── test_api.py
├── ui/
│   └── streamlit_app.py      <- Streamlit frontend
├── main.py                   <- FastAPI app entry point
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

**Structure Decision**: Single project with clean layer separation —
API → Agents → Services → Core. No monorepo needed at this scale.

## Complexity Tracking

No constitution violations to justify.
