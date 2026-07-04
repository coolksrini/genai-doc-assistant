from app.agents.graph import AgentState
from app.services.embedding import get_vector_store
from app.utils.logging import get_logger

logger = get_logger(__name__)


def retriever_node(state: AgentState) -> AgentState:
    store = get_vector_store()
    top_k = state.get("top_k", 5)
    results = store.similarity_search(state["question"], k=top_k)

    chunks = [
        {
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "page": doc.metadata.get("page", 0),
        }
        for doc in results
    ]

    sources = [
        {
            "document_name": c["source"],
            "chunk_index": c["chunk_index"],
            "excerpt": c["text"][:200],
        }
        for c in chunks
    ]

    trace = state.get("agent_trace", [])
    trace.append(f"Retriever: Retrieved {len(chunks)} chunk(s) from vector store")
    logger.info("Retriever node executed", extra={"chunks": len(chunks)})
    return {**state, "chunks": chunks, "sources": sources, "agent_trace": trace}
