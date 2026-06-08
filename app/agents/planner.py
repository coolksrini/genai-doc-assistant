from app.agents.graph import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

UNSAFE_PATTERNS = ["ignore previous", "disregard", "jailbreak", "you are now"]


def planner_node(state: AgentState) -> AgentState:
    question = state["question"].strip()

    for pattern in UNSAFE_PATTERNS:
        if pattern.lower() in question.lower():
            raise ValueError(f"Unsafe prompt detected: '{pattern}'")

    trace = state.get("agent_trace", [])
    trace.append(f"Planner: Analysing question — '{question[:80]}'")
    logger.info("Planner node executed", extra={"question": question[:80]})
    return {**state, "agent_trace": trace}
