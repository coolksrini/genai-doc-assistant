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

    def add_chunks(self, chunks: list[Document]) -> int:
        self._store.add_documents(chunks)
        logger.info("Added chunks to vector store", extra={"count": len(chunks)})
        return len(chunks)

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
