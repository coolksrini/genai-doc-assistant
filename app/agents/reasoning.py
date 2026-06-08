from app.agents.graph import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)


def reasoning_node(state: AgentState) -> AgentState:
    chunks = state.get("chunks", [])
    if not chunks:
        context = ""
    else:
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(f"[Source {i}: {c['source']} chunk {c['chunk_index']}]\n{c['text']}")
        context = "\n\n---\n\n".join(parts)

    trace = state.get("agent_trace", [])
    trace.append(f"Reasoning: Synthesised context from {len(chunks)} chunk(s)")
    logger.info("Reasoning node executed", extra={"context_len": len(context)})
    return {**state, "context": context, "agent_trace": trace}
