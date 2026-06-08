# Tasks: GenAI Document Q&A System

**Input**: Design documents from `specs/001-genai-document-qa/`
**Date**: 2026-06-08

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on each other)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Each task includes an exact file path

---

## Phase 1: Setup

**Purpose**: Project scaffold, environment, and tooling

- [ ] T001 Create full folder structure per plan.md (`app/api/`, `app/agents/`, `app/services/`, `app/core/`, `app/utils/`, `data/`, `tests/unit/`, `tests/integration/`, `ui/`)
- [ ] T002 Create `requirements.txt` with all dependencies (langchain, langchain-community, langchain-ollama, langgraph, chromadb, fastapi, uvicorn, streamlit, pypdf2, pandas, openpyxl, pyyaml, python-multipart, pytest, httpx, pydantic-settings)
- [ ] T003 Create `.env.example` with all env vars (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, EMBED_MODEL, CHROMA_PATH, MAX_FILE_SIZE_MB, CHUNK_SIZE, CHUNK_OVERLAP)
- [ ] T004 Create `.gitignore` (data/, .env, __pycache__, .venv, *.pyc, chroma_db/)
- [ ] T005 Create `tests/fixtures/` with one sample file per supported format (sample.pdf, sample.txt, sample.csv, sample.xlsx, sample.json, sample.yaml)
- [ ] T006 [P] Create all `__init__.py` files for app/, app/api/, app/agents/, app/services/, app/core/, app/utils/, tests/, tests/unit/, tests/integration/

**Checkpoint**: `pip install -r requirements.txt` succeeds; folder structure matches plan.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure all user stories depend on. MUST complete before any story work.

- [ ] T007 Implement `app/core/config.py` — pydantic `Settings` class loading all env vars with defaults; singleton `get_settings()` function
- [ ] T008 Implement `app/core/llm.py` — `get_llm()` factory returning `ChatOpenAI` pointed at `LLM_BASE_URL`; `get_embeddings()` factory returning `OllamaEmbeddings` with `EMBED_MODEL`
- [ ] T009 Implement `app/utils/logging.py` — structured JSON logger; `get_logger(name)` function; JSON format with timestamp, level, message, extra fields
- [ ] T010 Implement `app/services/embedding.py` — `VectorStore` class wrapping `Chroma`; `add_chunks(chunks, metadata)`, `similarity_search(query, k)`, `collection_empty()` methods; reads `CHROMA_PATH` from config
- [ ] T011 Create `main.py` — FastAPI app instance with CORS middleware, JSON error handlers, and router mounting; `uvicorn` entrypoint

**Checkpoint**: `python main.py` starts without errors; `GET /health` not yet implemented but app loads cleanly

---

## Phase 3: User Story 1 — Upload and Query a Document (P1) MVP

**Goal**: User uploads a PDF and gets a grounded answer with source citations.

**Independent Test**: `curl -X POST /upload-document -F file=@tests/fixtures/sample.pdf` returns ingested status; `curl -X POST /ask-questions -d '{"question":"..."}'` returns grounded answer with sources.

### Implementation

- [ ] T012 [US1] Implement `app/services/ingestion.py` — `load_document(file_path, format)` dispatch function; PDF loader using `pypdf2` returning list of `LangChain Document` objects
- [ ] T013 [US1] Implement `app/services/chunking.py` — `chunk_documents(docs)` using `RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)`; attaches source metadata to each chunk
- [ ] T014 [US1] Implement `app/agents/planner.py` — `planner_node(state: AgentState)` that parses the question and appends `"Planner: ..."` to `state["agent_trace"]`; returns updated state
- [ ] T015 [US1] Implement `app/agents/retriever.py` — `retriever_node(state: AgentState)` that embeds `state["question"]`, calls `VectorStore.similarity_search()`, populates `state["chunks"]` and `state["sources"]`
- [ ] T016 [US1] Implement `app/agents/reasoning.py` — `reasoning_node(state: AgentState)` that formats retrieved chunks into a context string stored in `state["context"]`; adds trace entry
- [ ] T017 [US1] Implement `app/agents/response.py` — `response_node(state: AgentState)` that calls LLM with grounded prompt (answer ONLY from context); sets `state["answer"]` and `state["is_grounded"]`; refusal message if no chunks
- [ ] T018 [US1] Implement `app/agents/graph.py` — `AgentState` TypedDict; `build_graph()` returning compiled `StateGraph` with nodes: planner → retriever → reasoning → response; edges sequential
- [ ] T019 [US1] Implement `app/api/routes.py` — `POST /upload-document`: validate file type/size, save to `data/`, call ingestion + chunking + embedding, return document metadata; `GET /health`: return `{"status":"ok","version":"1.0.0"}`
- [ ] T020 [US1] Add `POST /ask-questions` to `app/api/routes.py` — validate non-empty question, check collection not empty, invoke agent graph, return Answer response model
- [ ] T021 [US1] Write `tests/unit/test_ingestion.py` — test PDF loader returns non-empty Document list; test chunking produces chunks with metadata
- [ ] T022 [US1] Write `tests/unit/test_agents.py` — test each agent node in isolation with mocked AgentState; assert state fields populated correctly
- [ ] T023 [US1] Write `tests/integration/test_api.py` — test `/health` 200; test upload valid PDF 200; test ask grounded question returns is_grounded=true; test empty question returns 400

**Checkpoint**: All Scenario 1–4 from quickstart.md pass with `sample.pdf`

---

## Phase 4: User Story 2 — Multi-Format Document Support (P2)

**Goal**: All 6 formats (PDF, TXT, CSV, Excel, JSON, YAML) upload and return grounded answers.

**Independent Test**: Upload one file of each format; each returns `"status":"ingested"` and a question about its content returns a grounded answer.

### Implementation

- [ ] T024 [P] [US2] Add TXT loader to `app/services/ingestion.py` — read plain text file via `pathlib`; wrap in `LangChain Document`
- [ ] T025 [P] [US2] Add CSV loader to `app/services/ingestion.py` — `pandas.read_csv()`; convert each row to a Document with row index metadata
- [ ] T026 [P] [US2] Add Excel loader to `app/services/ingestion.py` — `pandas.read_excel()` with `openpyxl` engine; same row-to-Document conversion
- [ ] T027 [P] [US2] Add JSON loader to `app/services/ingestion.py` — stdlib `json.load()`; flatten nested structure to text; wrap in Document
- [ ] T028 [P] [US2] Add YAML loader to `app/services/ingestion.py` — `pyyaml.safe_load()`; convert to text representation; wrap in Document
- [ ] T029 [US2] Update file-type validation in `app/api/routes.py` to whitelist: `.pdf`, `.txt`, `.csv`, `.xlsx`, `.json`, `.yaml`
- [ ] T030 [US2] Write `tests/unit/test_ingestion.py` additions — one test per new format; assert non-empty Document list returned

**Checkpoint**: Scenario 8 from quickstart.md passes (all 6 formats upload successfully)

---

## Phase 5: User Story 3 — Multi-Agent Reasoning Pipeline (P2)

**Goal**: Complex multi-part questions produce coherent, validated answers via the full 4-agent pipeline.

**Independent Test**: Ask a complex multi-part question; verify `agent_trace` in response shows all 4 agents ran; verify answer is coherent and grounded.

### Implementation

- [ ] T031 [US3] Add output verifier node `app/agents/response.py` — after LLM response, check if answer references document content; if similarity score below threshold, override with refusal; update `is_grounded`
- [ ] T032 [US3] Add guardrail check to `app/agents/planner.py` — detect off-topic or unsafe prompts (empty after strip, injection patterns); raise `ValueError` caught at route level
- [ ] T033 [US3] Update `app/agents/graph.py` — add conditional edge after response node: if `is_grounded=False` short-circuit; ensure all 4 agent traces logged in `agent_trace`
- [ ] T034 [US3] Write `tests/unit/test_agents.py` additions — test guardrail rejects off-topic prompt; test verifier sets `is_grounded=False` when no relevant chunks

**Checkpoint**: Scenario 3 (multi-agent trace visible in response) and Scenario 4 (refusal on out-of-scope) from quickstart.md pass

---

## Phase 6: User Story 4 — Health Check & Observability (P3)

**Goal**: Operators can confirm system health; all errors appear as structured JSON logs.

**Independent Test**: `GET /health` returns 200; trigger an error, verify JSON log appears.

### Implementation

- [ ] T035 [US4] Integrate JSON logger from `app/utils/logging.py` into all routes in `app/api/routes.py` — log every request (method, path, status) and every error (exception type, message, stack omitted from response)
- [ ] T036 [US4] Add FastAPI exception handlers in `main.py` — `RequestValidationError` → 422 JSON; `HTTPException` → pass-through; unhandled `Exception` → 500 JSON with safe message; never expose stack trace in response
- [ ] T037 [US4] Add Ollama connectivity check to `GET /health` — attempt `llm.invoke("ping")`; return `{"status":"degraded","llm":"unavailable"}` if it fails; still HTTP 200

**Checkpoint**: Scenario 1 and Scenario 6 (error returns JSON not stack trace) from quickstart.md pass

---

## Phase 7: User Story 5 — Streamlit UI (P3)

**Goal**: Non-technical users can upload documents and ask questions through a web browser.

**Independent Test**: Open `http://localhost:8501`, upload a file, ask a question, see grounded answer with sources — no API knowledge needed.

### Implementation

- [ ] T038 [US5] Implement `ui/streamlit_app.py` — sidebar: file uploader (accepted types: pdf/txt/csv/xlsx/json/yaml) calling `POST /upload-document`; show success/error toast; main area: text input for question, submit button calling `POST /ask-questions`
- [ ] T039 [US5] Add answer display in `ui/streamlit_app.py` — render answer text; render sources as expandable cards (document name + excerpt); show `agent_trace` in a collapsed "Agent Steps" expander
- [ ] T040 [US5] Add connection config to `ui/streamlit_app.py` — `API_BASE_URL` from env var (default `http://localhost:8000`); show error if health check fails on app start

**Checkpoint**: Scenario 9 from quickstart.md passes end-to-end in browser

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Deployment, documentation, and final validation

- [ ] T041 [P] Create `Dockerfile` — multi-stage build; stage 1: install deps; stage 2: copy app, expose port 8000, CMD `uvicorn main:app`
- [ ] T042 [P] Create `docker-compose.yml` — `api` service (FastAPI) + `ui` service (Streamlit); shared `data/` volume; env_file `.env`
- [ ] T043 [P] Update `CLAUDE.md` Compound Engineering Log — document key learnings from implementation (library quirks, decisions made, patterns established)
- [ ] T044 Run all 9 scenarios from `specs/001-genai-document-qa/quickstart.md` and record results
- [ ] T045 Run full test suite `pytest tests/ -v` and confirm all pass
- [ ] T046 [P] Create `README.md` at project root — setup instructions, architecture diagram (ASCII), API usage, limitations, deployment steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1 MVP)**: Depends on Phase 2 — highest priority, implement first
- **Phase 4 (US2)**: Depends on Phase 2; can start after Phase 3 is complete
- **Phase 5 (US3)**: Depends on Phase 3 (extends agent graph from US1)
- **Phase 6 (US4)**: Depends on Phase 2; can run in parallel with Phase 4/5
- **Phase 7 (US5)**: Depends on Phase 3 (calls the API built in US1)
- **Phase 8 (Polish)**: Depends on all stories complete

### Parallel Opportunities Within Stories

```
Phase 2:  T007, T008, T009 can run in parallel (different files)
Phase 3:  T014, T015, T016, T017 can run in parallel (different agent files)
          T021, T022, T023 can run in parallel (different test files)
Phase 4:  T024, T025, T026, T027, T028 all run in parallel (different loaders)
Phase 8:  T041, T042, T043, T046 run in parallel
```

---

## Implementation Strategy

### MVP (Phase 1 + 2 + 3 only)

Complete T001–T023. At this point:
- PDF upload works
- Q&A with grounded answers works
- All unit + integration tests pass
- Health check works
- **Stop and validate before adding more formats or UI**

### Incremental After MVP

1. Add multi-format support (Phase 4) → validate Scenario 8
2. Harden agent reasoning (Phase 5) → validate Scenarios 3 & 4
3. Add observability (Phase 6) → validate Scenario 1
4. Add Streamlit UI (Phase 7) → validate Scenario 9
5. Polish + deploy (Phase 8)

---

## Task Summary

| Phase | Story | Tasks | Parallelizable |
|---|---|---|---|
| 1 Setup | — | T001–T006 | T003, T006 |
| 2 Foundation | — | T007–T011 | T007, T008, T009 |
| 3 Upload + Q&A | US1 (P1) | T012–T023 | T014–T017, T021–T023 |
| 4 Multi-format | US2 (P2) | T024–T030 | T024–T028 |
| 5 Agents | US3 (P2) | T031–T034 | T031, T032 |
| 6 Observability | US4 (P3) | T035–T037 | — |
| 7 Streamlit UI | US5 (P3) | T038–T040 | — |
| 8 Polish | — | T041–T046 | T041–T043, T046 |

**Total**: 46 tasks | **MVP scope**: T001–T023 (23 tasks)
