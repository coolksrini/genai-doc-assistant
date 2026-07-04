from typing import TypedDict, Any
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    question: str
    top_k: int
    plan: list[str]
    chunks: list[dict[str, Any]]
    context: str
    answer: str
    sources: list[dict[str, Any]]
    is_grounded: bool
    agent_trace: list[str]


def build_graph():
    from app.agents.planner import planner_node
    from app.agents.retriever import retriever_node
    from app.agents.reasoning import reasoning_node
    from app.agents.response import response_node, verifier_node

    graph = StateGraph(AgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("response", response_node)
    graph.add_node("verifier", verifier_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "reasoning")
    graph.add_edge("reasoning", "response")
    # Conditional: only run verifier when response claims to be grounded
    graph.add_conditional_edges(
        "response",
        lambda s: "verify" if s.get("is_grounded") else "end",
        {"verify": "verifier", "end": END},
    )
    graph.add_edge("verifier", END)

    return graph.compile()
