# Feature Specification: GenAI Document Q&A System

**Feature Branch**: `001-genai-document-qa`

**Created**: 2026-06-08

**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload and Query a Document (Priority: P1)

A user uploads an enterprise document (PDF, CSV, Excel, TXT, JSON, or YAML) and
asks a natural language question about its contents. The system retrieves the most
relevant sections and returns a grounded, cited answer.

**Why this priority**: This is the entire value proposition of the system. Without
document upload and Q&A, nothing else matters.

**Independent Test**: Upload a sample PDF, ask "What is the total revenue?", verify
the answer comes from the document content and includes a source reference.

**Acceptance Scenarios**:

1. **Given** a user has a PDF document, **When** they upload it via the API and ask
   a question, **Then** the system returns an answer grounded in the document with
   the source chunk cited.
2. **Given** a document has been uploaded, **When** the user asks a question whose
   answer is NOT in the document, **Then** the system responds with "I could not
   find this information in the uploaded documents."
3. **Given** an uploaded CSV file, **When** the user asks a data-related question,
   **Then** the system correctly retrieves and summarizes the relevant rows.

---

### User Story 2 - Multi-Format Document Support (Priority: P2)

A user can upload documents in any of the supported formats (PDF, TXT, CSV, Excel,
JSON, YAML) and receive consistent Q&A behavior regardless of format.

**Why this priority**: Enterprise environments have heterogeneous document formats.
Supporting multiple formats makes the system practically useful.

**Independent Test**: Upload one file of each format, ask the same type of question
for each, verify all return grounded answers.

**Acceptance Scenarios**:

1. **Given** an Excel spreadsheet, **When** uploaded and queried, **Then** the
   system treats rows/columns as structured document chunks.
2. **Given** an unsupported file type (e.g., .mp4), **When** a user attempts to
   upload it, **Then** the system rejects it with a clear error message listing
   accepted formats.
3. **Given** a file exceeding 10MB, **When** a user attempts to upload it,
   **Then** the system rejects it with a size limit error.

---

### User Story 3 - Multi-Agent Reasoning Pipeline (Priority: P2)

When a user submits a complex question, the system uses five AI agents
(Planner, Retriever, Reasoning, Response, Verifier) working in sequence to produce a
high-quality, validated answer.

**Why this priority**: The agentic pipeline is the technical centrepiece of the
capstone and differentiates the system from a simple RAG lookup.

**Independent Test**: Ask a multi-part question requiring synthesis across multiple
document sections; verify the answer is coherent, grounded, and validates against
the document content.

**Acceptance Scenarios**:

1. **Given** a complex question spanning multiple topics, **When** submitted,
   **Then** the Planner breaks it into sub-tasks, Retriever fetches relevant
   chunks, Reasoning synthesizes them, and Response generates the final answer.
2. **Given** any question, **When** the output verification agent flags the
   response as unsafe or off-topic, **Then** the system refuses to return that
   response and explains why.

---

### User Story 4 - Health Check & System Observability (Priority: P3)

An operator can confirm the system is running and healthy via a health endpoint,
and all requests/errors are logged in a structured format for debugging.

**Why this priority**: Required for deployment and production reliability.

**Independent Test**: Call `GET /health`, verify 200 response. Trigger an
intentional error, verify it appears in logs as structured JSON.

**Acceptance Scenarios**:

1. **Given** the system is running, **When** `GET /health` is called, **Then**
   it returns HTTP 200 with a status payload.
2. **Given** any request that causes an error, **When** the error occurs, **Then**
   it is logged as structured JSON (never a raw stack trace to the user).

---

### User Story 5 - Streamlit UI for Document Q&A (Priority: P3)

A non-technical user can interact with the system through a web UI — uploading
documents and asking questions without knowing the API.

**Why this priority**: Makes the system accessible for demonstration and evaluation.

**Independent Test**: Open the Streamlit UI, upload a document, type a question,
receive an answer — all without touching the API directly.

**Acceptance Scenarios**:

1. **Given** the UI is open, **When** a user drags a file to the upload widget,
   **Then** it is ingested and a confirmation message is shown.
2. **Given** a document is ingested, **When** the user types a question and
   submits, **Then** the answer appears with source references highlighted.

---

### Edge Cases

- What happens when the same document is uploaded twice? (System should deduplicate
  or overwrite gracefully, not create duplicate embeddings.)
- What happens when Ollama is not running? (System should return a clear service
  unavailable error, not hang indefinitely.)
- What happens when a document is 0 bytes or corrupted? (System should reject with
  a descriptive validation error.)
- What happens when a question is empty or only whitespace? (System should reject
  at the API boundary before reaching the LLM.)
- What happens when ChromaDB has no documents yet and a question is asked? (System
  should respond that no documents have been ingested.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept document uploads in PDF, TXT, CSV, Excel (.xlsx),
  JSON, and YAML formats via `POST /upload-document`.
- **FR-002**: System MUST reject files larger than 10MB with an HTTP 413 error and
  descriptive message.
- **FR-003**: System MUST reject unsupported file types with an HTTP 415 error
  listing accepted formats.
- **FR-004**: System MUST chunk uploaded documents into segments of ~500 tokens
  with 50-token overlap, embed each chunk using a local embedding model, and store
  in a vector database.
- **FR-005**: System MUST retrieve the top-N most semantically relevant chunks for
  any user question using cosine similarity search.
- **FR-006**: System MUST pass retrieved chunks through a five-agent pipeline
  (Planner → Retriever → Reasoning → Response → Verifier) to produce the final
  answer.
- **FR-007**: System MUST instruct the LLM to answer ONLY from the retrieved
  context — responses not supported by the documents MUST be declined.
- **FR-008**: System MUST include a source reference (document name + chunk
  identifier) in every successful answer.
- **FR-009**: System MUST expose `GET /health` returning HTTP 200 when operational.
- **FR-010**: System MUST log all requests and errors as structured JSON — raw
  stack traces MUST NOT be returned to API clients.
- **FR-011**: System MUST validate that question text is non-empty before
  processing.
- **FR-012**: System MUST be configurable via environment variables for LLM
  provider, model, embedding model, and vector store path — no hardcoded values.
- **FR-013**: System MUST provide a Streamlit UI allowing document upload and
  question submission without direct API knowledge.

### Key Entities

- **Document**: Uploaded file with metadata (name, format, upload timestamp, chunk
  count). Source of all grounded answers.
- **Chunk**: A ~500-token segment of a document with 50-token overlap, stored with
  embedding vector and metadata (source document, position).
- **Question**: User-submitted natural language query with non-empty text.
- **Answer**: LLM-generated response grounded in retrieved chunks, with source
  citations. May be a refusal if no relevant chunks found.
- **Agent**: One of five specialized reasoning units (Planner, Retriever,
  Reasoning, Response, Verifier) in the processing pipeline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can upload a document and receive a grounded answer to a
  relevant question within 30 seconds on local hardware.
- **SC-002**: 100% of questions about content not present in any uploaded document
  result in a refusal response (no hallucinated answers).
- **SC-003**: All six supported file formats (PDF, TXT, CSV, Excel, JSON, YAML)
  can be uploaded and queried successfully.
- **SC-004**: Invalid inputs (wrong file type, oversized file, empty question) are
  rejected at the API boundary with descriptive error messages in 100% of cases.
- **SC-005**: The system starts from a clean state and produces a working Q&A
  session in under 5 minutes of setup time.
- **SC-006**: All four agents (Planner, Retriever, Reasoning, Response) can be
  tested independently with mocked inputs.

## Assumptions

- Users run the system locally with Ollama installed and llama3.2 + nomic-embed-text
  models pulled.
- Documents are in English. Multi-language support is out of scope for v1.
- Concurrent multi-user support is out of scope — the system is designed for a
  single user or small team demo.
- The vector database is local (ChromaDB on disk); cloud vector store is out of
  scope for v1 but the interface must be swappable.
- Authentication/authorization is out of scope for v1 (no user accounts or API
  keys required to use the system).
- Mobile UI is out of scope — Streamlit desktop browser is sufficient for capstone
  demonstration.
