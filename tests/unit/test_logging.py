import json
import logging
import pytest
from app.utils.logging import get_logger, JsonFormatter


@pytest.mark.unit
def test_get_logger_returns_logger():
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


@pytest.mark.unit
def test_logger_has_json_formatter():
    logger = get_logger("test.formatter")
    handlers = logger.handlers
    assert any(isinstance(h.formatter, JsonFormatter) for h in handlers)


@pytest.mark.unit
def test_json_formatter_output(capsys):
    logger = get_logger("test.output")
    logger.info("hello world")
    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    assert record["message"] == "hello world"
    assert record["level"] == "INFO"
    assert "timestamp" in record
    assert "logger" in record


@pytest.mark.unit
def test_json_formatter_safe_extra(capsys):
    logger = get_logger("test.extra")
    logger.info("test extra", extra={"doc_name": "report.pdf", "count": 42})
    captured = capsys.readouterr()
    record = json.loads(captured.out.strip())
    assert record["doc_name"] == "report.pdf"
    assert record["count"] == 42


@pytest.mark.unit
def test_reserved_key_filename_not_used(capsys):
    """Regression: 'filename' is reserved in LogRecord — must use 'doc_name'."""
    logger = get_logger("test.reserved")
    # This should NOT raise KeyError
    logger.info("safe log", extra={"doc_name": "safe.pdf"})
    captured = capsys.readouterr()
    assert "safe.pdf" in captured.out
