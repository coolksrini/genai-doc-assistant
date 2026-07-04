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

VERIFY_PROMPT = """You are a grounding verifier. Determine if the ANSWER below is directly supported by the CONTEXT.

CONTEXT:
{context}

ANSWER:
{answer}

Reply with exactly ONE word: YES if the answer is supported by the context, NO if it is not.
Do not explain. Only YES or NO."""


def response_node(state: AgentState) -> AgentState:
    context = state.get("context", "")
    trace = state.get("agent_trace", [])

    if not context.strip():
        trace.append("Response: No relevant context found — returning refusal")
        return {**state, "answer": REFUSAL, "is_grounded": False, "sources": [], "agent_trace": trace}

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
    sources = state.get("sources", []) if is_grounded else []
    return {**state, "answer": answer, "is_grounded": is_grounded, "sources": sources, "agent_trace": trace}


def verifier_node(state: AgentState) -> AgentState:
    """
    Second-pass grounding check. Asks the LLM to verify its own answer
    against the retrieved context. Overrides to refusal if verification fails.
    """
    trace = state.get("agent_trace", [])

    # Skip verification if already a refusal or no context
    if not state.get("is_grounded") or not state.get("context", "").strip():
        trace.append("Verifier: Skipped (answer already a refusal)")
        return {**state, "agent_trace": trace}

    llm = get_llm()
    verify_msg = VERIFY_PROMPT.format(
        context=state["context"][:2000],  # cap context to stay within token budget
        answer=state["answer"],
    )
    verdict = llm.invoke([HumanMessage(content=verify_msg)]).content.strip().upper()

    if verdict.startswith("NO"):
        trace.append("Verifier: Answer not supported by context — overriding to refusal")
        logger.info("Verifier: overriding ungrounded answer")
        return {**state, "answer": REFUSAL, "is_grounded": False, "sources": [], "agent_trace": trace}

    trace.append(f"Verifier: Answer confirmed grounded (verdict={verdict})")
    logger.info("Verifier node executed", extra={"verdict": verdict})
    return {**state, "agent_trace": trace}
