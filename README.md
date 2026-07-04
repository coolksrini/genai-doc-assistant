# GenAI Document Assistant

A Generative AI-powered document Q&A system built for the **Edureka PGP GenAI & ML Capstone**. Upload enterprise documents in any format, ask natural language questions, and get answers grounded exclusively in your documents — powered by LangChain, LangGraph, ChromaDB, and Ollama.

---

## Architecture

```
User
 │
 ├── Streamlit UI  ──────────────────────────────────┐
 │                                                    │
 └── REST API (FastAPI)                               │
       │                                              │
       ├── POST /upload-document                      │
       │     └── Ingestion → Chunking → Embedding    │
       │                        │                     │
       │                   ChromaDB ◄─────────────── │
       │                                              │
       └── POST /ask-questions                        │
             └── LangGraph Pipeline                   │
                   ├── Planner   (guardrails)         │
                   ├── Retriever (cosine search)      │
                   ├── Reasoning (context synthesis)  │
                   ├── Response  (grounded LLM call)  │
                   └── Verifier  (second-pass check)  │
                                                      │
Ollama ◄──── LLM: llama3.2 / Embed: nomic-embed-text ┘
```

---

## Supported Document Formats

| Format | Parser |
|---|---|
| PDF | pypdf2 |
| TXT | stdlib |
| CSV | pandas |
| Excel (.xlsx) | pandas + openpyxl |
| JSON | stdlib |
| YAML | pyyaml |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) with models pulled:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Local Setup

```bash
# 1. Clone and enter
git clone https://github.com/coolksrini/genai-doc-assistant
cd genai-doc-assistant

# 2. Virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env          # defaults work for local Ollama

# 5. Start API
python main.py                # http://localhost:8000

# 6. Start UI (separate terminal)
streamlit run ui/streamlit_app.py   # http://localhost:8501
```

### Docker

```bash
cp .env.example .env
docker compose up --build
# API → http://localhost:8000
# UI  → http://localhost:8501
```

---

## API Reference

### `GET /health`
```json
{
  "status": "ok",
  "version": "1.0.0",
  "llm": "available",
  "vector_store": "ready"
}
```
Always HTTP 200. `status` is `"ok"` or `"degraded"`.

### `POST /upload-document`
Multipart form — field: `file`.

```bash
curl -X POST http://localhost:8000/upload-document \
     -F "file=@annual_report.pdf"
```
```json
{ "document_id": "...", "filename": "annual_report.pdf", "chunk_count": 42, "status": "ingested" }
```

### `POST /ask-questions`
```bash
curl -X POST http://localhost:8000/ask-questions \
     -H "Content-Type: application/json" \
     -d '{"question": "What was the Q3 revenue?", "top_k": 5}'
```
```json
{
  "question": "What was the Q3 revenue?",
  "answer": "According to the document, Q3 revenue was $4.2 million.",
  "is_grounded": true,
  "sources": [{ "document_name": "annual_report.pdf", "chunk_index": 12, "excerpt": "..." }],
  "agent_trace": ["Planner: ...", "Retriever: ...", "Reasoning: ...", "Response: ...", "Verifier: ..."]
}
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `LLM_API_KEY` | `ollama` | API key (`ollama` for local) |
| `LLM_MODEL` | `llama3.2` | Chat model |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `CHROMA_PATH` | `./data/chroma_db` | Vector store path |
| `MAX_FILE_SIZE_MB` | `10` | Upload size limit |
| `CHUNK_SIZE` | `200` | Chunk size in tokens |
| `CHUNK_OVERLAP` | `20` | Overlap between chunks |

**Switching to OpenAI/Groq** — change only these two env vars, no code changes:

```bash
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
```

---

## Running Tests

```bash
# Fast (no Ollama needed)
pytest tests/unit/ -m unit

# Integration (Ollama embed required)
pytest tests/integration/ -m integration

# E2E — full pipeline with sample datasets
pytest tests/e2e/ -m e2e

# Regression — grounding + format regression
pytest tests/regression/ -m regression

# Everything
pytest tests/
```

---

## Agent Roles

| Agent | Responsibility |
|---|---|
| **Planner** | Validates question; detects prompt injection (15 patterns) |
| **Retriever** | Embeds question; cosine similarity search → top-K chunks |
| **Reasoning** | Synthesises retrieved chunks into a structured context |
| **Response** | LLM call with grounded-only prompt; refusal if no context |
| **Verifier** | Second LLM pass (YES/NO): confirms answer is context-supported |

---

## Limitations

- **Single user**: no concurrent user isolation; shared vector store
- **English only**: multi-language documents not tested
- **No authentication**: no API keys or user accounts for v1
- **Local model accuracy**: llama3.2 (3B) may miss precise numeric extractions from dense docs
- **PDF tables**: tabular data in PDFs extracted as plain text (may lose structure)
- **10 MB upload limit**: large documents must be split before uploading

---

## Security Considerations

- All inputs validated at the API boundary (file type whitelist, size cap)
- Prompt injection detection in Planner (15 patterns)
- LLM instructed to answer only from retrieved context
- Second-pass Verifier rejects answers not supported by context
- Stack traces never returned to API clients; logged internally only
- `.env` excluded from git; use environment variables in production

---

## Project Structure

```
genai-doc-assistant/
├── app/
│   ├── agents/          # LangGraph nodes (planner, retriever, reasoning, response+verifier)
│   ├── api/             # FastAPI routes
│   ├── core/            # Config, LLM + embedding factories
│   ├── services/        # Document ingestion, chunking, ChromaDB embedding
│   └── utils/           # Structured JSON logger
├── data/sample_docs/    # Sample datasets for testing
├── specs/               # Spec Kit: spec, plan, tasks, research, contracts
├── tests/               # unit / integration / e2e / regression
├── ui/                  # Streamlit frontend
├── Dockerfile
├── docker-compose.yml
├── main.py
└── CLAUDE.md            # Living development guide (Compound Engineering)
```

---

## Built With

- [LangChain](https://python.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/) — agent orchestration
- [ChromaDB](https://www.trychroma.com/) — local vector store
- [Ollama](https://ollama.com) — local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) — REST API
- [Streamlit](https://streamlit.io/) — web UI
- [GitHub Spec Kit](https://github.com/github/spec-kit) — spec-driven development
