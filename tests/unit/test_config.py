import pytest
from app.core.config import get_settings, Settings


@pytest.mark.unit
def test_defaults():
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_model == "llama3.2"
    assert s.chunk_size == 500
    assert s.chunk_overlap == 50
    assert s.max_file_size_mb == 10


@pytest.mark.unit
def test_env_override(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    monkeypatch.setenv("CHUNK_SIZE", "512")
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_model == "gpt-4o"
    assert s.chunk_size == 512
    get_settings.cache_clear()


@pytest.mark.unit
def test_singleton():
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
