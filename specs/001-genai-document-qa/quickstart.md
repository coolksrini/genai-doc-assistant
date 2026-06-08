# Quickstart Validation Guide

**Date**: 2026-06-08

This guide proves the system works end-to-end. Run these scenarios after
implementation to validate each requirement.

## Prerequisites

1. Ollama running with required models:
   ```bash
   ollama serve &
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

2. Python virtual environment activated with dependencies installed:
   ```bash
   python -m venv .venv && source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. Environment configured:
   ```bash
   cp .env.example .env
   # defaults work for local Ollama — no edits needed
   ```

4. App running:
   ```bash
   python main.py
   # FastAPI available at http://localhost:8000
   # Streamlit available at http://localhost:8501 (separate terminal: streamlit run ui/streamlit_app.py)
   ```

---

## Scenario 1: Health Check (FR-009)

```bash
curl http://localhost:8000/health
```

**Expected**: HTTP 200, `{"status": "ok", "version": "1.0.0"}`

---

## Scenario 2: Upload a PDF (FR-001, FR-004)

```bash
curl -X POST http://localhost:8000/upload-document \
  -F "file=@tests/fixtures/sample.pdf"
```

**Expected**: HTTP 200, response includes `"status": "ingested"` and
`"chunk_count"` > 0.

---

## Scenario 3: Ask a Grounded Question (FR-005, FR-006, FR-007, FR-008)

```bash
curl -X POST http://localhost:8000/ask-questions \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the document?"}'
```

**Expected**: HTTP 200, `"is_grounded": true`, `"sources"` is non-empty,
`"answer"` does not contain information beyond what's in the document.

---

## Scenario 4: Refusal on Out-of-Scope Question (FR-007)

```bash
curl -X POST http://localhost:8000/ask-questions \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'
```

**Expected**: HTTP 200, `"is_grounded": false`,
`"answer"` = "I could not find this information in the uploaded documents."

---

## Scenario 5: Reject Oversized File (FR-002)

```bash
# Create a dummy 11MB file
dd if=/dev/zero bs=1m count=11 | gzip > /tmp/big.pdf
curl -X POST http://localhost:8000/upload-document -F "file=@/tmp/big.pdf"
```

**Expected**: HTTP 413, `"detail"` mentions size limit.

---

## Scenario 6: Reject Unsupported Format (FR-003)

```bash
curl -X POST http://localhost:8000/upload-document \
  -F "file=@tests/fixtures/sample.mp4"
```

**Expected**: HTTP 415, `"detail"` lists accepted formats.

---

## Scenario 7: Reject Empty Question (FR-011)

```bash
curl -X POST http://localhost:8000/ask-questions \
  -H "Content-Type: application/json" \
  -d '{"question": "   "}'
```

**Expected**: HTTP 400, `"detail"` = "Question must not be empty."

---

## Scenario 8: Multi-Format Upload (FR-001)

Upload one file of each format and verify each returns `"status": "ingested"`:

```bash
curl -X POST http://localhost:8000/upload-document -F "file=@tests/fixtures/sample.txt"
curl -X POST http://localhost:8000/upload-document -F "file=@tests/fixtures/sample.csv"
curl -X POST http://localhost:8000/upload-document -F "file=@tests/fixtures/sample.xlsx"
curl -X POST http://localhost:8000/upload-document -F "file=@tests/fixtures/sample.json"
curl -X POST http://localhost:8000/upload-document -F "file=@tests/fixtures/sample.yaml"
```

**Expected**: All return HTTP 200 with `"status": "ingested"`.

---

## Scenario 9: Streamlit UI (FR-013)

1. Open `http://localhost:8501` in a browser
2. Drag a PDF to the upload widget → confirm "Ingested successfully" message
3. Type a question in the text box → confirm answer appears with source citations

**Expected**: Full Q&A cycle works without touching the API directly.

---

## Automated Tests

Run the full test suite:
```bash
pytest tests/ -v
```

**Expected**: All unit tests and integration tests pass.
