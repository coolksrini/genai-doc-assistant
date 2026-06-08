from pathlib import Path
import pytest
from app.services.ingestion import load_document
from app.services.chunking import chunk_documents

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_pdf_loader_returns_documents():
    docs = load_document(FIXTURES / "sample.pdf", "sample.pdf")
    assert len(docs) > 0
    assert all(d.page_content.strip() for d in docs)
    assert all(d.metadata.get("source") == "sample.pdf" for d in docs)


def test_txt_loader():
    docs = load_document(FIXTURES / "sample.txt", "sample.txt")
    assert isinstance(docs, list)


def test_csv_loader():
    docs = load_document(FIXTURES / "sample.csv", "sample.csv")
    assert len(docs) > 0
    assert "Alice" in docs[0].page_content or any("Alice" in d.page_content for d in docs)


def test_excel_loader():
    docs = load_document(FIXTURES / "sample.xlsx", "sample.xlsx")
    assert len(docs) > 0


def test_json_loader():
    docs = load_document(FIXTURES / "sample.json", "sample.json")
    assert len(docs) == 1
    assert "Acme" in docs[0].page_content


def test_yaml_loader():
    docs = load_document(FIXTURES / "sample.yaml", "sample.yaml")
    assert len(docs) == 1


def test_unsupported_format_raises(tmp_path):
    bad_file = tmp_path / "video.mp4"
    bad_file.write_bytes(b"fake")
    with pytest.raises(ValueError, match="Unsupported format"):
        load_document(bad_file, "video.mp4")


def test_chunking_produces_chunks_with_metadata():
    docs = load_document(FIXTURES / "sample.pdf", "sample.pdf")
    chunks = chunk_documents(docs)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata
        assert "source" in chunk.metadata
