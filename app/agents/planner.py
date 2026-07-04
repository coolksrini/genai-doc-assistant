from app.agents.graph import AgentState
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Prompt injection and role-hijacking patterns
UNSAFE_PATTERNS = [
    "ignore previous",
    "disregard",
    "jailbreak",
    "you are now",
    "pretend you are",
    "act as if",
    "act as though",
    "new instruction",
    "forget previous",
    "from now on you",
    "reveal your",
    "reveal the system",
    "print your instructions",
    "override instructions",
    "you must ignore",
]


def planner_node(state: AgentState) -> AgentState:
    question = state["question"].strip()

    if not question:
        raise ValueError("Question must not be empty.")

    q_lower = question.lower()
    for pattern in UNSAFE_PATTERNS:
        if pattern in q_lower:
            raise ValueError(f"Unsafe prompt detected: '{pattern}'")

    trace = state.get("agent_trace", [])
    trace.append(f"Planner: Analysing question — '{question[:80]}'")
    logger.info("Planner node executed", extra={"question": question[:80]})
    return {**state, "agent_trace": trace}
