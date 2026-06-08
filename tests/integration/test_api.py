from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_valid_pdf():
    with open(FIXTURES / "sample.pdf", "rb") as f:
        r = client.post("/upload-document", files={"file": ("sample.pdf", f, "application/pdf")})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ingested"
    assert data["chunk_count"] > 0


def test_upload_unsupported_format():
    r = client.post(
        "/upload-document",
        files={"file": ("video.mp4", b"fake content", "video/mp4")},
    )
    assert r.status_code == 415
    assert "Unsupported" in r.json()["detail"]


def test_upload_oversized_file():
    big = b"x" * (11 * 1024 * 1024)
    r = client.post(
        "/upload-document",
        files={"file": ("big.pdf", big, "application/pdf")},
    )
    assert r.status_code == 413
    assert "limit" in r.json()["detail"]


def test_ask_empty_question():
    r = client.post("/ask-questions", json={"question": "   "})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()
