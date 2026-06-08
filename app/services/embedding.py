from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.core.config import get_settings
from app.core.llm import get_embeddings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self):
        s = get_settings()
        self._store = Chroma(
            collection_name="documents",
            embedding_function=get_embeddings(),
            persist_directory=s.chroma_path,
        )

    def add_chunks(self, chunks: list[Document], batch_size: int = 100) -> int:
        """Add chunks in batches to avoid overwhelming the embedding model."""
        total = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            self._store.add_documents(batch)
            total += len(batch)
        logger.info("Added chunks to vector store", extra={"count": total})
        return total

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self._store.similarity_search(query, k=k)

    def collection_empty(self) -> bool:
        return self._store._collection.count() == 0


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
