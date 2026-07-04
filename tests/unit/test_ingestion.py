from pathlib import Path
import pytest
from app.services.ingestion import load_document, SUPPORTED_FORMATS
from app.services.chunking import chunk_documents

FIXTURES = Path(__file__).parent.parent / "fixtures"
SAMPLE_DOCS = Path(__file__).parent.parent.parent / "data" / "sample_docs"


# ---------- format coverage ----------

@pytest.mark.unit
def test_pdf_loader_returns_documents():
    docs = load_document(FIXTURES / "sample.pdf", "sample.pdf")
    assert len(docs) > 0
    assert all(d.page_content.strip() for d in docs)
    assert all(d.metadata["source"] == "sample.pdf" for d in docs)


@pytest.mark.unit
def test_txt_loader():
    docs = load_document(FIXTURES / "sample.txt", "sample.txt")
    assert isinstance(docs, list)
    assert len(docs) == 1


@pytest.mark.unit
def test_csv_loader_produces_one_doc_per_row():
    docs = load_document(FIXTURES / "sample.csv", "sample.csv")
    assert len(docs) >= 3  # header + 3 data rows
    assert any("Alice" in d.page_content for d in docs)


@pytest.mark.unit
def test_excel_loader():
    docs = load_document(FIXTURES / "sample.xlsx", "sample.xlsx")
    assert len(docs) > 0


@pytest.mark.unit
def test_json_loader():
    docs = load_document(FIXTURES / "sample.json", "sample.json")
    assert len(docs) == 1
    assert "Acme" in docs[0].page_content


@pytest.mark.unit
def test_yaml_loader():
    docs = load_document(FIXTURES / "sample.yaml", "sample.yaml")
    assert len(docs) == 1
    assert len(docs[0].page_content) > 0


@pytest.mark.unit
def test_unsupported_format_raises(tmp_path):
    bad = tmp_path / "video.mp4"
    bad.write_bytes(b"fake")
    with pytest.raises(ValueError, match="Unsupported format"):
        load_document(bad, "video.mp4")


@pytest.mark.unit
def test_supported_formats_set():
    assert ".pdf" in SUPPORTED_FORMATS
    assert ".txt" in SUPPORTED_FORMATS
    assert ".csv" in SUPPORTED_FORMATS
    assert ".xlsx" in SUPPORTED_FORMATS
    assert ".json" in SUPPORTED_FORMATS
    assert ".yaml" in SUPPORTED_FORMATS
    assert ".mp4" not in SUPPORTED_FORMATS


# ---------- metadata correctness ----------

@pytest.mark.unit
def test_loader_attaches_source_to_metadata():
    for suffix in ["sample.pdf", "sample.txt", "sample.csv",
                   "sample.xlsx", "sample.json", "sample.yaml"]:
        docs = load_document(FIXTURES / suffix, suffix)
        assert all(d.metadata.get("source") == suffix for d in docs), \
            f"Missing source metadata in {suffix}"


# ---------- chunking after loading ----------

@pytest.mark.unit
def test_chunking_produces_chunks_with_metadata():
    docs = load_document(FIXTURES / "sample.pdf", "sample.pdf")
    chunks = chunk_documents(docs)
    assert len(chunks) > 0
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata
        assert "source" in chunk.metadata


# ---------- sample dataset loaders (skipped if not present) ----------

@pytest.mark.unit
def test_real_pdf_loads(sample_docs_dir):
    pdf = sample_docs_dir / "attention_is_all_you_need.pdf"
    docs = load_document(pdf, pdf.name)
    assert len(docs) > 5, "Expected multi-page PDF"
    full_text = " ".join(d.page_content for d in docs)
    assert "attention" in full_text.lower()


@pytest.mark.unit
def test_real_csv_loads(sample_docs_dir):
    csv = sample_docs_dir / "titanic.csv"
    docs = load_document(csv, csv.name)
    assert len(docs) >= 891  # 891 passengers


@pytest.mark.unit
def test_real_excel_loads(sample_docs_dir):
    xl = sample_docs_dir / "world_happiness_2023.xlsx"
    docs = load_document(xl, xl.name)
    assert len(docs) > 0
    full_text = " ".join(d.page_content for d in docs)
    assert "Finland" in full_text


@pytest.mark.unit
def test_real_json_loads(sample_docs_dir):
    j = sample_docs_dir / "nobel_prizes.json"
    docs = load_document(j, j.name)
    assert len(docs) == 1
    assert "Physics" in docs[0].page_content or "Nobel" in docs[0].page_content


@pytest.mark.unit
def test_real_yaml_loads(sample_docs_dir):
    y = sample_docs_dir / "nobel_physics_laureates.yaml"
    docs = load_document(y, y.name)
    assert len(docs) == 1
    assert "physics" in docs[0].page_content.lower()


@pytest.mark.unit
def test_real_txt_loads(sample_docs_dir):
    t = sample_docs_dir / "artificial_intelligence.txt"
    docs = load_document(t, t.name)
    assert len(docs) == 1
    assert len(docs[0].page_content) > 10_000
