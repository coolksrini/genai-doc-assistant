"""
Regression tests: grounding guarantees must never break.

These tests lock in the core safety invariant — the LLM must NEVER
return fabricated information presented as fact. Every release must pass.

Run: pytest tests/regression/test_grounding.py -m regression -v
"""
import pytest
from tests.conftest import ask

pytestmark = pytest.mark.regression

OUT_OF_SCOPE_QUESTIONS = [
    "Who won the 2022 FIFA World Cup?",
    "What is the capital of Mars?",
    "What is the latest iPhone model released in 2025?",
    "Tell me about quantum computing breakthroughs in 2024",
    "What is the current stock price of Apple?",
]


class TestGroundingInvariants:
    @pytest.mark.parametrize("question", OUT_OF_SCOPE_QUESTIONS)
    def test_out_of_scope_never_fabricates(self, ingested_client, question):
        """
        Regression: questions outside document scope must return refusal.
        The LLM must NOT answer from its training data.
        """
        result = ask(ingested_client, question)
        assert result["is_grounded"] is False or \
               "could not find" in result["answer"].lower(), \
               f"Possible hallucination for '{question}': {result['answer'][:200]}"

    def test_grounded_answer_always_has_sources(self, ingested_client):
        """Regression: every is_grounded=True answer must have at least one source."""
        result = ask(ingested_client, "What is the attention mechanism?")
        if result["is_grounded"]:
            assert len(result["sources"]) > 0, \
                "Grounded answer must always include source citations"

    def test_refusal_answer_text_is_consistent(self, ingested_client):
        """Regression: refusal message must be the canonical string."""
        from app.agents.response import REFUSAL
        result = ask(ingested_client, "What is the population of Jupiter?")
        if not result["is_grounded"]:
            assert result["answer"] == REFUSAL, \
                f"Refusal answer changed. Expected: '{REFUSAL}', Got: '{result['answer']}'"

    def test_empty_sources_on_refusal(self, ingested_client):
        """Regression: refusal must have empty sources list."""
        result = ask(ingested_client, "Who won the 2024 Super Bowl?")
        if not result["is_grounded"]:
            assert result["sources"] == [], \
                f"Refusal should have no sources, got: {result['sources']}"

    def test_agent_trace_never_empty(self, ingested_client):
        """Regression: agent_trace must always be populated."""
        result = ask(ingested_client, "What is AI?")
        assert len(result["agent_trace"]) >= 2, \
            "agent_trace must always have at least Planner + Response entries"
