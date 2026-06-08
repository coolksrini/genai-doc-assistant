from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.graph import AgentState
from app.core.llm import get_llm
from app.utils.logging import get_logger

logger = get_logger(__name__)

REFUSAL = "I could not find this information in the uploaded documents."

SYSTEM_PROMPT = """You are a document assistant. Answer the user's question using ONLY the context below.
If the answer is not present in the context, respond with exactly:
"{refusal}"
Do not use any outside knowledge. Do not guess.""".format(refusal=REFUSAL)


def response_node(state: AgentState) -> AgentState:
    context = state.get("context", "")
    trace = state.get("agent_trace", [])

    if not context.strip():
        trace.append("Response: No relevant context found — returning refusal")
        return {**state, "answer": REFUSAL, "is_grounded": False, "agent_trace": trace}

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {state['question']}"),
    ]

    llm = get_llm()
    result = llm.invoke(messages)
    answer = result.content.strip()

    is_grounded = REFUSAL.lower() not in answer.lower()
    if not is_grounded:
        answer = REFUSAL

    trace.append(f"Response: Generated answer (grounded={is_grounded})")
    logger.info("Response node executed", extra={"is_grounded": is_grounded, "answer_len": len(answer)})
    return {**state, "answer": answer, "is_grounded": is_grounded, "agent_trace": trace}
