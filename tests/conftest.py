"""
Shared fixtures for all test layers.

Isolation strategy:
- Unit tests: no external deps, all mocked
- Integration tests: FastAPI TestClient, isolated ChromaDB in tmp_path
- E2E tests: FastAPI TestClient, isolated ChromaDB, real Ollama required
- Regression tests: same as E2E, run full format matrix
"""
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SAMPLE_DOCS = Path(__file__).parent.parent / "data" / "sample_docs"
FIXTURES = Path(__file__).parent / "fixtures"


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: fast unit tests, no external deps")
    config.addinivalue_line("markers", "integration: FastAPI client, isolated DB")
    config.addinivalue_line("markers", "e2e: requires Ollama + sample datasets")
    config.addinivalue_line("markers", "regression: full format regression suite")


@pytest.fixture(scope="session")
def sample_docs_dir() -> Path:
    if not SAMPLE_DOCS.exists():
        pytest.skip("Sample docs not found — run data download script first")
    return SAMPLE_DOCS


@pytest.fixture()
def isolated_client(tmp_path, monkeypatch):
    """FastAPI test client with isolated ChromaDB in tmp_path."""
    chroma_dir = str(tmp_path / "chroma_test")
    monkeypatch.setenv("CHROMA_PATH", chroma_dir)

    # Reset singleton vector store so it picks up new path
    import app.services.embedding as emb_mod
    emb_mod._store = None

    # Reset lru_cache on settings so env var is re-read
    from app.core.config import get_settings
    get_settings.cache_clear()

    from main import app
    client = TestClient(app)
    yield client

    # Cleanup
    emb_mod._store = None
    get_settings.cache_clear()
    if Path(chroma_dir).exists():
        shutil.rmtree(chroma_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def ingested_client(tmp_path_factory, sample_docs_dir):
    """
    Module-scoped client with ALL 6 sample docs pre-ingested.
    Used by E2E and regression tests to avoid re-ingesting per test.
    """
    chroma_dir = str(tmp_path_factory.mktemp("chroma_e2e"))
    os.environ["CHROMA_PATH"] = chroma_dir

    import app.services.embedding as emb_mod
    emb_mod._store = None
    from app.core.config import get_settings
    get_settings.cache_clear()

    from main import app
    client = TestClient(app)

    # Ingest all 6 sample docs
    for path in sorted(sample_docs_dir.iterdir()):
        if path.suffix.lower() in {".pdf", ".txt", ".csv", ".xlsx", ".json", ".yaml"}:
            with open(path, "rb") as f:
                r = client.post("/upload-document", files={"file": (path.name, f)})
            assert r.status_code == 200, f"Failed to ingest {path.name}: {r.text}"

    yield client

    emb_mod._store = None
    get_settings.cache_clear()
    shutil.rmtree(chroma_dir, ignore_errors=True)
    if "CHROMA_PATH" in os.environ:
        del os.environ["CHROMA_PATH"]


def ask(client: TestClient, question: str, top_k: int = 5) -> dict:
    """Helper: POST /ask-questions and return parsed JSON."""
    r = client.post("/ask-questions", json={"question": question, "top_k": top_k})
    assert r.status_code == 200, f"ask failed ({r.status_code}): {r.text}"
    return r.json()
