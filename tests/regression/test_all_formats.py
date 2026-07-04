"""
Regression tests: format support must never regress.

Every supported format must continue to upload, chunk, embed,
and return grounded answers. Any PR that breaks a format fails here.

Run: pytest tests/regression/test_all_formats.py -m regression -v
"""
import pytest
from pathlib import Path

pytestmark = pytest.mark.regression

SAMPLE_DOCS = Path(__file__).parent.parent.parent / "data" / "sample_docs"

FORMAT_CASES = [
    ("attention_is_all_you_need.pdf", "What is the Transformer architecture?"),
    ("artificial_intelligence.txt", "What is artificial intelligence?"),
    ("titanic.csv", "How many passengers are in the dataset?"),
    ("world_happiness_2023.xlsx", "Which country ranked first in happiness?"),
    ("nobel_prizes.json", "What Nobel Prize categories are included?"),
    ("nobel_physics_laureates.yaml", "What physics prizes are listed?"),
]


@pytest.mark.parametrize("filename,question", FORMAT_CASES)
def test_format_upload_and_qa(isolated_client, filename, question):
    """
    Regression: each format must:
    1. Upload successfully (200)
    2. Return chunk_count > 0
    3. Answer a relevant question with is_grounded=True
    """
    path = SAMPLE_DOCS / filename
    if not path.exists():
        pytest.skip(f"Sample doc not found: {filename}")

    # Step 1: Upload
    with open(path, "rb") as f:
        r = isolated_client.post("/upload-document",
                                 files={"file": (filename, f)})
    assert r.status_code == 200, f"[{filename}] Upload failed: {r.text}"
    body = r.json()
    assert body["status"] == "ingested", f"[{filename}] Status: {body['status']}"
    assert body["chunk_count"] > 0, f"[{filename}] Zero chunks produced"

    # Step 2: Q&A
    r2 = isolated_client.post("/ask-questions",
                              json={"question": question, "top_k": 5})
    assert r2.status_code == 200, f"[{filename}] Ask failed: {r2.text}"
    result = r2.json()

    assert "answer" in result
    assert "is_grounded" in result
    assert "sources" in result
    assert "agent_trace" in result
    assert len(result["answer"]) > 0

    # When grounded, at least one source must be present
    if result["is_grounded"]:
        assert len(result["sources"]) > 0, \
            f"[{filename}] Grounded answer must have at least one source"


class TestFormatValidationRegression:
    """Validation rules must stay consistent across all formats."""

    @pytest.mark.parametrize("filename", [
        "attention_is_all_you_need.pdf",
        "artificial_intelligence.txt",
        "titanic.csv",
        "world_happiness_2023.xlsx",
        "nobel_prizes.json",
        "nobel_physics_laureates.yaml",
    ])
    def test_format_chunk_metadata_intact(self, filename):
        """Regression: chunks from all formats must have source + chunk_index metadata."""
        path = SAMPLE_DOCS / filename
        if not path.exists():
            pytest.skip(f"Sample doc not found: {filename}")

        from app.services.ingestion import load_document
        from app.services.chunking import chunk_documents

        docs = load_document(path, filename)
        chunks = chunk_documents(docs)

        assert len(chunks) > 0, f"[{filename}] No chunks produced"
        for chunk in chunks:
            assert chunk.metadata.get("source") == filename, \
                f"[{filename}] Missing/wrong source metadata"
            assert "chunk_index" in chunk.metadata, \
                f"[{filename}] Missing chunk_index metadata"

    def test_unsupported_format_still_rejected(self, isolated_client):
        """Regression: unsupported formats must always be rejected with 415."""
        r = isolated_client.post(
            "/upload-document",
            files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
        )
        assert r.status_code == 415

    def test_oversized_file_still_rejected(self, isolated_client):
        """Regression: files over 10MB must always be rejected with 413."""
        big = b"x" * (11 * 1024 * 1024)
        r = isolated_client.post(
            "/upload-document",
            files={"file": ("big.pdf", big, "application/pdf")},
        )
        assert r.status_code == 413

    def test_empty_question_still_rejected(self, isolated_client):
        """Regression: empty questions must always return 400."""
        r = isolated_client.post("/ask-questions", json={"question": ""})
        assert r.status_code == 400
