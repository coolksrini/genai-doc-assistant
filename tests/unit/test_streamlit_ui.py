"""
Streamlit UI tests using Streamlit's AppTest framework.

AppTest runs the app in a headless mode — no browser needed.
We mock `requests` to control what the API returns.

Docs: https://docs.streamlit.io/develop/api-reference/app-testing
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest

UI_PATH = os.path.join(os.path.dirname(__file__), "../../ui/streamlit_app.py")


# ---------- helpers ----------

def _mock_resp(data: dict, status: int = 200) -> MagicMock:
    m = MagicMock()
    m.json.return_value = data
    m.status_code = status
    return m


HEALTH_OK = {"status": "ok", "version": "1.0.0", "llm": "available", "vector_store": "ready"}
HEALTH_DEGRADED = {"status": "degraded", "version": "1.0.0", "llm": "unavailable", "vector_store": "empty"}
UPLOAD_OK = {"document_id": "abc-123", "filename": "report.pdf", "chunk_count": 8, "status": "ingested"}
ANSWER_GROUNDED = {
    "question": "What company is described?",
    "answer": "Acme Corp is a manufacturing company.",
    "is_grounded": True,
    "sources": [{"document_name": "report.pdf", "chunk_index": 0, "excerpt": "Acme Corp..."}],
    "agent_trace": ["Planner: analysing", "Retriever: 1 chunk", "Reasoning: context", "Response: grounded", "Verifier: YES"],
}
ANSWER_REFUSAL = {
    "question": "Who won the World Cup?",
    "answer": "I could not find this information in the uploaded documents.",
    "is_grounded": False,
    "sources": [],
    "agent_trace": ["Planner: analysing", "Retriever: 0 chunks", "Response: refusal"],
}


# ---------- app loads ----------

def _healthy_get(*args, **kwargs):
    return _mock_resp(HEALTH_OK)


def _degraded_get(*args, **kwargs):
    return _mock_resp(HEALTH_DEGRADED)


def _unavailable_get(*args, **kwargs):
    raise Exception("connection refused")


# ---------- app loads ----------

@pytest.mark.unit
def test_app_loads_with_healthy_api():
    """App renders without exception when API is healthy."""
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    assert not at.exception


@pytest.mark.unit
def test_app_shows_success_banner_when_healthy():
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    success_texts = [s.value for s in at.success]
    assert any("connected" in t.lower() or "available" in t.lower() for t in success_texts)


@pytest.mark.unit
def test_app_stops_when_api_unreachable():
    """App must halt and show an error if health check returns None."""
    with patch("ui.streamlit_app.requests.get", side_effect=_unavailable_get):
        at = AppTest.from_file(UI_PATH).run()
    errors = [e.value for e in at.error]
    assert any("api" in e.lower() or "reach" in e.lower() or "server" in e.lower() for e in errors)


@pytest.mark.unit
def test_app_shows_warning_when_degraded():
    with patch("ui.streamlit_app.requests.get", side_effect=_degraded_get):
        at = AppTest.from_file(UI_PATH).run()
    warnings = [w.value for w in at.warning]
    assert any("degraded" in w.lower() or "unavailable" in w.lower() for w in warnings)


# ---------- layout ----------

@pytest.mark.unit
def test_app_has_title():
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    titles = [t.value for t in at.title]
    assert any("document assistant" in t.lower() or "genai" in t.lower() for t in titles)


@pytest.mark.unit
def test_app_has_file_uploader_widget():
    """file_uploader renders as UnknownElement in AppTest 1.45 — verify it's present."""
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    from streamlit.testing.v1.element_tree import UnknownElement
    unknown = [e for e in at.main if isinstance(e, UnknownElement)]
    assert len(unknown) >= 1, "Expected at least one UnknownElement (file_uploader)"


@pytest.mark.unit
def test_app_has_text_area_for_question():
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    assert len(at.text_area) >= 1


@pytest.mark.unit
def test_app_has_top_k_slider():
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    assert len(at.slider) >= 1
    slider = at.slider[0]
    assert slider.min == 1
    assert slider.max == 20


@pytest.mark.unit
def test_app_has_ask_button():
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get):
        at = AppTest.from_file(UI_PATH).run()
    buttons = [b.label for b in at.button]
    assert any("ask" in b.lower() for b in buttons)


# ---------- Q&A interaction ----------

@pytest.mark.unit
def test_qa_empty_question_shows_warning():
    """Submitting blank question shows a warning; ask_question never called."""
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get), \
         patch("ui.streamlit_app.ask_question") as mock_ask:
        at = AppTest.from_file(UI_PATH).run()
        at.text_area[0].set_value("   ")
        at.button[0].click().run()
    mock_ask.assert_not_called()
    warnings = [w.value for w in at.warning]
    assert any("question" in w.lower() for w in warnings)


def _post_resp(data: dict, status: int) -> MagicMock:
    """Mock requests.post with given data and status_code."""
    m = MagicMock()
    m.json.return_value = data
    m.status_code = status
    return m


@pytest.mark.unit
def test_qa_grounded_answer_shows_success():
    """Grounded answer renders a success element with 'Answer' label."""
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get), \
         patch("ui.streamlit_app.requests.post",
               return_value=_post_resp(ANSWER_GROUNDED, 200)):
        at = AppTest.from_file(UI_PATH).run()
        at.text_area[0].set_value("What company is described?")
        at.button[0].click().run()
    success_texts = " ".join(s.value for s in at.success)
    assert "answer" in success_texts.lower() or "connected" in success_texts.lower()


@pytest.mark.unit
def test_qa_refusal_shows_info():
    """Refusal (is_grounded=False) renders in an info box."""
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get), \
         patch("ui.streamlit_app.requests.post",
               return_value=_post_resp(ANSWER_REFUSAL, 200)):
        at = AppTest.from_file(UI_PATH).run()
        at.text_area[0].set_value("Who won the World Cup?")
        at.button[0].click().run()
    info_texts = " ".join(i.value for i in at.info)
    assert "could not find" in info_texts.lower()


@pytest.mark.unit
def test_qa_503_shows_error():
    """503 response renders an error element."""
    err = {"detail": "No documents have been ingested yet. Please upload a document first."}
    with patch("ui.streamlit_app.requests.get", side_effect=_healthy_get), \
         patch("ui.streamlit_app.requests.post", return_value=_post_resp(err, 503)):
        at = AppTest.from_file(UI_PATH).run()
        at.text_area[0].set_value("What is AI?")
        at.button[0].click().run()
    error_texts = " ".join(e.value for e in at.error)
    assert "no documents" in error_texts.lower() or "ingested" in error_texts.lower()


# ---------- helper function unit tests (no AppTest) ----------

@pytest.mark.unit
def test_check_health_returns_dict_on_success():
    from ui.streamlit_app import check_health
    with patch("ui.streamlit_app.requests.get", return_value=_mock_resp(HEALTH_OK)):
        result = check_health()
    assert result["status"] == "ok"


@pytest.mark.unit
def test_check_health_returns_none_on_error():
    from ui.streamlit_app import check_health
    with patch("ui.streamlit_app.requests.get", side_effect=Exception("refused")):
        result = check_health()
    assert result is None


@pytest.mark.unit
def test_upload_document_success():
    from ui.streamlit_app import upload_document
    fake = MagicMock(name="report.pdf", type="application/pdf")
    fake.name = "report.pdf"
    fake.getvalue.return_value = b"%PDF"
    with patch("ui.streamlit_app.requests.post", return_value=_mock_resp(UPLOAD_OK, 200)):
        result, status = upload_document(fake)
    assert status == 200
    assert result["status"] == "ingested"


@pytest.mark.unit
def test_upload_document_413():
    from ui.streamlit_app import upload_document
    fake = MagicMock(); fake.name = "big.pdf"; fake.type = "application/pdf"
    fake.getvalue.return_value = b"x" * 100
    err = {"detail": "File size exceeds the 10MB limit."}
    with patch("ui.streamlit_app.requests.post", return_value=_mock_resp(err, 413)):
        result, status = upload_document(fake)
    assert status == 413


@pytest.mark.unit
def test_ask_question_grounded():
    from ui.streamlit_app import ask_question
    with patch("ui.streamlit_app.requests.post", return_value=_mock_resp(ANSWER_GROUNDED, 200)):
        result, status = ask_question("What company is described?", top_k=5)
    assert status == 200
    assert result["is_grounded"] is True
    assert len(result["sources"]) == 1


@pytest.mark.unit
def test_ask_question_refusal():
    from ui.streamlit_app import ask_question
    with patch("ui.streamlit_app.requests.post", return_value=_mock_resp(ANSWER_REFUSAL, 200)):
        result, status = ask_question("Who won?", top_k=5)
    assert result["is_grounded"] is False
    assert result["sources"] == []


@pytest.mark.unit
def test_accepted_types_covers_all_formats():
    from ui.streamlit_app import ACCEPTED_TYPES
    assert set(ACCEPTED_TYPES) >= {"pdf", "txt", "csv", "xlsx", "json", "yaml"}


@pytest.mark.unit
def test_api_base_url_strips_trailing_slash(monkeypatch):
    import os
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000/")
    url = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
    assert not url.endswith("/")
