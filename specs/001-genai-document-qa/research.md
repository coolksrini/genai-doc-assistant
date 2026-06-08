# Research: GenAI Document Q&A System

**Phase**: 0 — Pre-planning research
**Date**: 2026-06-08

## Decision 1: Agent Framework — LangChain + LangGraph

**Decision**: Use LangChain for RAG chains and LangGraph for multi-agent orchestration.

**Rationale**: LangGraph's `StateGraph` is the cleanest way to implement the
four-agent pipeline (Planner → Retriever → Reasoning → Response) as a directed
graph with typed state. Each node is a pure function, making agents independently
testable. LangChain's document loaders, text splitters, and vector store
integrations eliminate boilerplate in the service layer.

**Alternatives considered**:
- LlamaIndex: Excellent RAG abstractions but weaker multi-agent graph support.
  ReActAgent works but is less transparent than LangGraph's explicit node model.
- AWS Strands: Great for AWS-native deployments but adds cloud dependency to dev.

---

## Decision 2: LLM & Embedding Provider — Ollama (dev) / OpenAI-compatible (prod)

**Decision**: Use `langchain-ollama` with llama3.2 (LLM) and nomic-embed-text
(embeddings) for development. Production swaps via `LLM_BASE_URL` env var to
any OpenAI-compatible endpoint.

**Rationale**: Ollama provides a fully local, free, reproducible dev environment.
The `ChatOpenAI(base_url=..., api_key=...)` pattern in LangChain makes the swap
trivial — one env var change, zero code changes. llama3.2 (3B) is fast enough
for local dev; nomic-embed-text is the best-performing local embedding model for
English documents.

**Alternatives considered**:
- GPT-4o directly: Costs money per request during development iteration.
- Hugging Face local models: More complex setup, less Ollama-style simplicity.

---

## Decision 3: Vector Store — ChromaDB

**Decision**: ChromaDB as the default vector store, accessed through
LangChain's `Chroma` wrapper.

**Rationale**: ChromaDB is developer-friendly, runs fully in-process (no separate
server needed), and persists to disk automatically. LangChain's `Chroma` wrapper
means we can swap to `Pinecone`, `FAISS`, or `Weaviate` by changing one import
and the constructor arguments — the rest of the code is identical.

**Alternatives considered**:
- FAISS: Faster but in-memory only (no built-in persistence); requires manual
  serialization.
- Pinecone: Best for scale but requires cloud account and API key — conflicts
  with Local-First principle (Constitution IV).

---

## Decision 4: Chunking Strategy — RecursiveCharacterTextSplitter (200 tokens, 20 overlap)

**Decision**: Use LangChain's `RecursiveCharacterTextSplitter` with
`chunk_size=200` (tokens) and `chunk_overlap=20`.

**Rationale**: Recursive splitting respects natural text boundaries (paragraphs →
sentences → words) before falling back to hard splits, producing more semantically
coherent chunks than a naive fixed-size split. 200 tokens balances retrieval
precision (small enough to be specific) with context completeness (large enough
to be useful). 20-token overlap prevents answer truncation at chunk boundaries.

**Alternatives considered**:
- SemanticChunker: Better semantic coherence but slower and requires an extra
  embedding pass per ingestion.
- Fixed 512-token chunks: Too large — reduces retrieval precision.

---

## Decision 5: API Framework — FastAPI

**Decision**: FastAPI with `python-multipart` for file uploads and `uvicorn`
as the ASGI server.

**Rationale**: FastAPI's async support, automatic OpenAPI docs, Pydantic request
validation, and file upload handling make it the best Python choice for this
use case. Its `UploadFile` type handles streaming file validation cleanly.

**Alternatives considered**:
- Flask: Synchronous by default, less type safety, no automatic docs.
- Django: Heavyweight for a simple API service.

---

## Decision 6: Document Parsing Libraries

| Format | Library | Reason |
|--------|---------|--------|
| PDF    | `pypdf2` | Lightweight, instructor-specified, sufficient for text PDFs |
| TXT    | stdlib `pathlib` | No dependency needed |
| CSV    | `pandas.read_csv()` | Instructor-specified; handles encoding edge cases |
| Excel  | `pandas.read_excel()` + `openpyxl` | Instructor-specified combination |
| JSON   | stdlib `json` | No dependency needed |
| YAML   | `pyyaml` | Instructor-specified |

All loaders return a normalized list of `LangChain Document` objects so the
chunking and embedding pipeline is format-agnostic.

---

## Decision 7: Structured Logging — Python logging + JSON formatter

**Decision**: Use Python's stdlib `logging` with a custom JSON formatter.
No third-party logging library needed.

**Rationale**: Keeps dependencies minimal. JSON format enables log aggregation
in any cloud environment. Sufficient for capstone scope.

**Alternatives considered**:
- `structlog`: More features but adds a dependency.
- `loguru`: Cleaner API but also an additional dependency.
