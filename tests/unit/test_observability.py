"""
Unit tests for Phase 6 — observability and health check.
Tests exception handlers and health endpoint logic.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.unit
def test_health_returns_200_always():
    """Health must always return HTTP 200 even when degraded."""
    r = client.get("/health")
    assert r.status_code == 200


@pytest.mark.unit
def test_health_response_schema():
    r = client.get("/health")
    body = r.json()
    assert "status" in body
    assert "version" in body
    assert "llm" in body
    assert "vector_store" in body
    assert body["version"] == "1.0.0"


@pytest.mark.unit
def test_health_ok_when_llm_available():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="pong")
    with patch("app.api.routes.get_llm", return_value=fake_llm), \
         patch("app.api.routes.get_vector_store") as mock_vs:
        mock_vs.return_value.collection_empty.return_value = False
        r = client.get("/health")
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm"] == "available"
    assert body["vector_store"] == "ready"


@pytest.mark.unit
def test_health_degraded_when_llm_unavailable():
    with patch("app.api.routes.get_llm", side_effect=Exception("Ollama down")), \
         patch("app.api.routes.get_vector_store") as mock_vs:
        mock_vs.return_value.collection_empty.return_value = True
        r = client.get("/health")
    body = r.json()
    assert r.status_code == 200          # still 200
    assert body["status"] == "degraded"
    assert body["llm"] == "unavailable"


@pytest.mark.unit
def test_health_vector_store_empty():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="pong")
    with patch("app.api.routes.get_llm", return_value=fake_llm), \
         patch("app.api.routes.get_vector_store") as mock_vs:
        mock_vs.return_value.collection_empty.return_value = True
        r = client.get("/health")
    body = r.json()
    assert body["vector_store"] == "empty"


@pytest.mark.unit
def test_health_vector_store_unavailable():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="pong")
    with patch("app.api.routes.get_llm", return_value=fake_llm), \
         patch("app.api.routes.get_vector_store", side_effect=Exception("ChromaDB down")):
        r = client.get("/health")
    body = r.json()
    assert body["vector_store"] == "unavailable"
    assert body["status"] == "degraded"


@pytest.mark.unit
def test_unhandled_exception_returns_safe_message():
    """Unhandled exceptions must never expose stack traces."""
    with patch("app.api.routes.get_vector_store", side_effect=RuntimeError("internal crash")):
        r = client.post("/ask-questions", json={"question": "hello"})
    assert r.status_code in {500, 503}
    body = r.json()
    assert "traceback" not in body.get("detail", "").lower()
    assert "runtimeerror" not in body.get("detail", "").lower()


@pytest.mark.unit
def test_validation_error_returns_422(isolated_client):
    """Pydantic validation errors return 422 with readable message."""
    r = isolated_client.post("/ask-questions", json={"question": 12345})  # wrong type
    assert r.status_code == 422
    assert "detail" in r.json()


@pytest.mark.unit
def test_request_logging_does_not_raise(isolated_client):
    """Middleware must complete without raising — verified by clean 200 response."""
    r = isolated_client.get("/health")
    assert r.status_code == 200  # middleware didn't crash
