# API Contracts: GenAI Document Q&A System

**Date**: 2026-06-08

All endpoints return `application/json`. Errors always include `{"detail": "..."}`.

---

## GET /health

**Purpose**: Liveness check for operators and deployment health probes.

**Request**: No body, no parameters.

**Response 200**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## POST /upload-document

**Purpose**: Upload and ingest an enterprise document into the vector store.

**Request**: `multipart/form-data`
| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | binary | Yes | The document file |

**Accepted formats**: `pdf`, `txt`, `csv`, `xlsx`, `json`, `yaml`
**Max size**: 10MB

**Response 200**:
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "annual_report.pdf",
  "chunk_count": 42,
  "status": "ingested"
}
```

**Response 413** (file too large):
```json
{
  "detail": "File size exceeds the 10MB limit. Received: 15.2MB"
}
```

**Response 415** (unsupported format):
```json
{
  "detail": "Unsupported file type '.mp4'. Accepted formats: pdf, txt, csv, xlsx, json, yaml"
}
```

**Response 422** (no file provided):
```json
{
  "detail": "No file provided in the request."
}
```

**Response 500** (ingestion failure):
```json
{
  "detail": "Document ingestion failed. Please check the file is not corrupted."
}
```

---

## POST /ask-questions

**Purpose**: Ask a natural language question against all ingested documents.

**Request**: `application/json`
```json
{
  "question": "What was the total revenue in Q3?",
  "top_k": 5
}
```

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `question` | string | Yes | — | Non-empty, stripped |
| `top_k` | integer | No | 5 | Range 1–20; chunks to retrieve |

**Response 200** (grounded answer):
```json
{
  "question": "What was the total revenue in Q3?",
  "answer": "According to the uploaded documents, the total revenue in Q3 was $4.2 million.",
  "is_grounded": true,
  "sources": [
    {
      "document_name": "annual_report.pdf",
      "chunk_index": 12,
      "excerpt": "Q3 total revenue reached $4.2 million, representing a 15% increase..."
    }
  ],
  "agent_trace": [
    "Planner: Identified single-fact retrieval task",
    "Retriever: Retrieved 5 chunks from 1 document",
    "Reasoning: Synthesized context from top 2 chunks",
    "Response: Generated grounded answer",
    "Verifier: Answer confirmed grounded"
  ]
}
```

**Response 200** (no relevant content — refusal):
```json
{
  "question": "Who won the 2022 World Cup?",
  "answer": "I could not find this information in the uploaded documents.",
  "is_grounded": false,
  "sources": [],
  "agent_trace": [
    "Planner: Identified factual lookup task",
    "Retriever: Retrieved 5 chunks, none relevant (similarity < threshold)",
    "Verifier: No grounding found — returning refusal"
  ]
}
```

**Response 400** (empty question):
```json
{
  "detail": "Question must not be empty."
}
```

**Response 503** (no documents ingested):
```json
{
  "detail": "No documents have been ingested yet. Please upload a document first."
}
```

**Response 503** (LLM unavailable):
```json
{
  "detail": "LLM service is unavailable. Please ensure Ollama is running."
}
```
