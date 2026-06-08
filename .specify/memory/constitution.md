<!--
Sync Impact Report
Version change: 0.0.0 (unset) → 1.0.0
Added sections: Core Principles (5), Tech Stack & Constraints, Development Workflow
Templates updated: plan-template.md ✅, spec-template.md ✅, tasks-template.md ✅
Deferred TODOs: none
-->

# genai-doc-assistant Constitution

## Core Principles

### I. Grounded Responses Only (NON-NEGOTIABLE)
The LLM MUST answer exclusively from retrieved document context — never from its
training data. Every response must cite the source chunk it was generated from.
Responses that cannot be grounded in retrieved content MUST be refused with a
clear message ("I could not find this information in the uploaded documents.").

**Rationale**: Prevents hallucination, which is the primary failure mode in
enterprise document Q&A systems. Grounding is the core value proposition.

### II. Modular Agent Architecture
The system MUST be composed of four independently testable, swappable agents:
Planner (decides steps), Retriever (fetches chunks), Reasoning (analyzes context),
Response (generates final answer). No agent may call another agent directly —
all orchestration goes through LangGraph. Each agent must be testable in isolation
with mocked inputs/outputs.

**Rationale**: Compound engineering requires each component to be independently
evolvable. Tight coupling between agents makes the system brittle and hard to
improve incrementally.

### III. Format-Agnostic Document Ingestion
The ingestion pipeline MUST support PDF, TXT, CSV, Excel, JSON, and YAML without
any agent or RAG component having direct knowledge of file format. Format parsing
is handled exclusively in the ingestion layer (app/services/). New formats MUST
be addable by adding a loader without touching any other component.

**Rationale**: Enterprise documents come in many formats. Coupling format logic
into the retrieval or agent layer makes format additions expensive.

### IV. Local-First, Cloud-Swap-Ready
All development and testing MUST work fully offline using Ollama (llama3.2 for
LLM, nomic-embed-text for embeddings). The LLM and embedding model MUST be
referenced only via configuration (environment variables), never hardcoded.
Swapping to OpenAI, Groq, or any OpenAI-compatible provider MUST require only
changing environment variables — zero code changes.

**Rationale**: Free, reproducible local development lowers the barrier to
iteration. Production swap via config makes deployment flexible.

### V. Safety & Validation at Every Boundary
All user inputs MUST be validated at the API boundary (file type whitelist:
pdf/txt/csv/xlsx/json/yaml; max file size: 10MB). The output MUST pass through
an output verification step before being returned. Errors MUST be logged
structurally (JSON logs) and return user-friendly messages — never raw stack
traces. Guardrails MUST reject unsafe or off-topic prompts before they reach
the LLM.

**Rationale**: Enterprise systems require predictability and safety. Unsafe
outputs or unhandled errors erode user trust immediately.

## Tech Stack & Constraints

- **Language**: Python 3.11+
- **Agent Framework**: LangChain + LangGraph (agent orchestration)
- **LLM (dev)**: Ollama — llama3.2 via OpenAI-compatible API (http://localhost:11434/v1)
- **LLM (prod)**: Any OpenAI-compatible provider (OpenAI, Groq) — swap via env vars
- **Embeddings (dev)**: nomic-embed-text via Ollama
- **Vector Store**: ChromaDB (dev/default); interface must be swappable to Pinecone/FAISS
- **API Layer**: FastAPI with endpoints: POST /upload-document, POST /ask-questions, GET /health
- **UI**: Streamlit (optional, connects to FastAPI backend)
- **Document Parsers**: pypdf2, pandas (CSV/Excel), openpyxl, json (stdlib), pyyaml
- **Deployment**: Docker (primary), Render (free cloud option)
- **Chunking**: 200-token fixed size with overlap; semantic boundary awareness

## Development Workflow (Compound Engineering)

This project follows the **Compound Engineering** methodology via **GitHub Spec Kit**:

1. **Specify** — write a spec for the feature/task (`/speckit-specify`)
2. **Plan** — generate an implementation plan (`/speckit-plan`)
3. **Tasks** — break into actionable tasks (`/speckit-tasks`)
4. **Implement** — AI executes each task (`/speckit-implement`)
5. **Compound** — document learnings, decisions, and gotchas back into `CLAUDE.md`

Each completed task MUST result in an update to `CLAUDE.md` capturing:
- What was built and why key decisions were made
- Any library quirks or version-specific behavior discovered
- Patterns established for future tasks to follow

**Branch strategy**: one feature branch per Spec Kit feature. PRs reviewed before merge.
**Commit style**: conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).
**Testing**: every agent and service MUST have at least one unit test before the
implement phase is marked complete.

## Governance

This constitution supersedes all other practices and preferences. Any deviation
from these principles requires amending this document first — not after the fact.

Amendment procedure:
1. Propose change with rationale in a PR description
2. Update this file and bump the version (MAJOR for principle removal/redefinition,
   MINOR for new principle, PATCH for clarifications)
3. Update `CLAUDE.md` to reflect the change

`CLAUDE.md` is the **runtime development guidance** file — it references this
constitution and accumulates task-by-task learnings. When in doubt, consult
`CLAUDE.md` first, then this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-06-08 | **Last Amended**: 2026-06-08
