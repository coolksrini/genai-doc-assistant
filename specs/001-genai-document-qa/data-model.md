# Data Model: GenAI Document Q&A System

**Phase**: 1 — Design
**Date**: 2026-06-08

## Entities

### Document
Represents an uploaded file before and after ingestion.

| Field | Type | Validation |
|---|---|---|
| `id` | UUID | Auto-generated on upload |
| `filename` | str | Non-empty, unique within collection |
| `format` | enum | pdf, txt, csv, xlsx, json, yaml |
| `size_bytes` | int | 1 ≤ size ≤ 10,485,760 (10MB) |
| `uploaded_at` | datetime | UTC, set on upload |
| `chunk_count` | int | Set after ingestion; 0 until ingested |
| `status` | enum | pending, ingested, failed |

### Chunk
A semantic segment of a Document stored as an embedding in ChromaDB.

| Field | Type | Notes |
|---|---|---|
| `id` | str | `{document_id}_{chunk_index}` |
| `document_id` | UUID | FK → Document |
| `document_name` | str | Denormalized for retrieval display |
| `chunk_index` | int | Position within document |
| `text` | str | Raw chunk text (≈200 tokens) |
| `embedding` | float[] | nomic-embed-text vector (768 dims) |
| `metadata` | dict | document_id, document_name, chunk_index |

### Question
A user-submitted natural language query.

| Field | Type | Validation |
|---|---|---|
| `text` | str | Non-empty, stripped of whitespace |
| `top_k` | int | Default 5; range 1–20 |
| `submitted_at` | datetime | UTC, set on receipt |

### Answer
The system's response to a Question.

| Field | Type | Notes |
|---|---|---|
| `question` | str | Echo of input question |
| `answer` | str | LLM-generated text or refusal message |
| `sources` | list[Source] | Chunks used to generate the answer |
| `is_grounded` | bool | False if refusal (no relevant chunks found) |
| `agent_trace` | list[str] | Steps taken by each agent (for transparency) |

### Source (embedded in Answer)
| Field | Type | Notes |
|---|---|---|
| `document_name` | str | Source document filename |
| `chunk_index` | int | Position in document |
| `excerpt` | str | First 200 chars of the chunk |

---

## Data Flow

```
Upload Flow:
  User → POST /upload-document
    → validate (type, size)
    → ingestion.py: load file → list[Document]
    → chunking.py: split → list[Chunk text]
    → embedding.py: embed chunks → store in ChromaDB
    → return: {document_id, chunk_count, status: "ingested"}

Query Flow:
  User → POST /ask-questions
    → validate (non-empty question)
    → LangGraph pipeline:
        Planner node   → parse question, decide retrieval strategy
        Retriever node → embed question → cosine search → top-K chunks
        Reasoning node → synthesize chunks → build context prompt
        Response node  → LLM call with grounded prompt → Answer
        Verifier node  → check answer is grounded → pass or refuse
    → return: Answer (with sources or refusal)
```

---

## State Schema (LangGraph)

```python
class AgentState(TypedDict):
    question: str            # user input
    plan: list[str]          # planner output: list of sub-tasks
    chunks: list[dict]       # retriever output: top-K chunks with metadata
    context: str             # reasoning output: synthesized context string
    answer: str              # response output: final answer text
    sources: list[dict]      # chunk citations
    is_grounded: bool        # verifier output
    agent_trace: list[str]   # step log for transparency
```

---

## ChromaDB Collection Schema

**Collection name**: `documents`

**Metadata fields per embedding**:
```json
{
  "document_id": "uuid-string",
  "document_name": "filename.pdf",
  "chunk_index": 0,
  "format": "pdf"
}
```

**Query**: cosine similarity on embedded question vector → top-K results
with metadata and distance score.
