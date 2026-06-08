import pytest
from unittest.mock import MagicMock, patch
from app.agents.graph import AgentState
from app.agents.planner import planner_node, UNSAFE_PATTERNS
from app.agents.reasoning import reasoning_node
from app.agents.response import response_node, REFUSAL


def _state(**overrides) -> AgentState:
    base = AgentState(
        question="What is the total revenue?",
        top_k=5,
        plan=[],
        chunks=[],
        context="",
        answer="",
        sources=[],
        is_grounded=False,
        agent_trace=[],
    )
    return {**base, **overrides}


# ---------- Planner ----------

@pytest.mark.unit
def test_planner_adds_trace():
    result = planner_node(_state())
    assert len(result["agent_trace"]) == 1
    assert "Planner" in result["agent_trace"][0]


@pytest.mark.unit
def test_planner_preserves_existing_trace():
    result = planner_node(_state(agent_trace=["prior step"]))
    assert len(result["agent_trace"]) == 2
    assert "prior step" in result["agent_trace"]


@pytest.mark.unit
@pytest.mark.parametrize("bad_prompt", UNSAFE_PATTERNS)
def test_planner_rejects_unsafe_prompts(bad_prompt):
    with pytest.raises(ValueError, match="Unsafe prompt"):
        planner_node(_state(question=f"please {bad_prompt} everything"))


@pytest.mark.unit
def test_planner_allows_normal_questions():
    result = planner_node(_state(question="Who won the Nobel Prize in Physics 2023?"))
    assert "Planner" in result["agent_trace"][0]


@pytest.mark.unit
def test_planner_strips_whitespace_in_trace():
    result = planner_node(_state(question="  What is AI?  "))
    assert result["agent_trace"][0].count("\n") == 0


# ---------- Reasoning ----------

@pytest.mark.unit
def test_reasoning_builds_context_from_chunks():
    chunks = [
        {"text": "Revenue was $4.2M in Q3", "source": "report.pdf", "chunk_index": 0, "page": 1},
        {"text": "Founded in 1990", "source": "report.pdf", "chunk_index": 1, "page": 1},
    ]
    result = reasoning_node(_state(chunks=chunks))
    assert "Revenue" in result["context"]
    assert "Founded" in result["context"]


@pytest.mark.unit
def test_reasoning_empty_chunks_gives_empty_context():
    result = reasoning_node(_state())
    assert result["context"] == ""


@pytest.mark.unit
def test_reasoning_adds_trace_entry():
    result = reasoning_node(_state())
    assert any("Reasoning" in t for t in result["agent_trace"])


@pytest.mark.unit
def test_reasoning_includes_source_labels():
    chunks = [{"text": "abc", "source": "myfile.csv", "chunk_index": 3, "page": 0}]
    result = reasoning_node(_state(chunks=chunks))
    assert "myfile.csv" in result["context"]
    assert "chunk 3" in result["context"]


# ---------- Response ----------

@pytest.mark.unit
def test_response_returns_refusal_when_no_context():
    result = response_node(_state(context=""))
    assert result["answer"] == REFUSAL
    assert result["is_grounded"] is False


@pytest.mark.unit
def test_response_calls_llm_when_context_present():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="Finland ranks first.")
    with patch("app.agents.response.get_llm", return_value=fake_llm):
        result = response_node(_state(
            context="Finland is ranked 1st with a score of 7.804.",
            question="Which country is happiest?"
        ))
    assert result["is_grounded"] is True
    assert "Finland" in result["answer"]
    fake_llm.invoke.assert_called_once()


@pytest.mark.unit
def test_response_marks_ungrounded_when_llm_returns_refusal():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content=REFUSAL)
    with patch("app.agents.response.get_llm", return_value=fake_llm):
        result = response_node(_state(
            context="Some unrelated content.",
            question="Who won the 2024 Olympics?"
        ))
    assert result["is_grounded"] is False
    assert result["answer"] == REFUSAL


@pytest.mark.unit
def test_response_adds_trace():
    fake_llm = MagicMock()
    fake_llm.invoke.return_value = MagicMock(content="Answer here.")
    with patch("app.agents.response.get_llm", return_value=fake_llm):
        result = response_node(_state(context="Some context."))
    assert any("Response" in t for t in result["agent_trace"])


# ---------- Graph ----------

@pytest.mark.unit
def test_graph_builds_without_error():
    from app.agents.graph import build_graph
    graph = build_graph()
    assert graph is not None
