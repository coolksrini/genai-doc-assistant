import pytest
from langchain_core.documents import Document
from app.services.chunking import chunk_documents


def _doc(text: str, source: str = "test.txt") -> Document:
    return Document(page_content=text, metadata={"source": source})


@pytest.mark.unit
def test_chunk_adds_index_metadata():
    docs = [_doc("word " * 500)]
    chunks = chunk_documents(docs)
    for chunk in chunks:
        assert "chunk_index" in chunk.metadata


@pytest.mark.unit
def test_chunk_preserves_source_metadata():
    docs = [_doc("Hello world " * 100, source="report.pdf")]
    chunks = chunk_documents(docs)
    assert all(c.metadata["source"] == "report.pdf" for c in chunks)


@pytest.mark.unit
def test_chunk_splits_long_text():
    long_text = "The quick brown fox jumped over the lazy dog. " * 100
    docs = [_doc(long_text)]
    chunks = chunk_documents(docs)
    assert len(chunks) > 1


@pytest.mark.unit
def test_chunk_short_text_stays_one():
    docs = [_doc("Short text.")]
    chunks = chunk_documents(docs)
    assert len(chunks) == 1


@pytest.mark.unit
def test_chunk_multiple_docs():
    docs = [_doc("word " * 300, source=f"doc{i}.txt") for i in range(3)]
    chunks = chunk_documents(docs)
    sources = {c.metadata["source"] for c in chunks}
    assert len(sources) == 3


@pytest.mark.unit
def test_chunk_indices_are_sequential():
    docs = [_doc("word " * 500)]
    chunks = chunk_documents(docs)
    indices = [c.metadata["chunk_index"] for c in chunks]
    assert indices == list(range(len(chunks)))
