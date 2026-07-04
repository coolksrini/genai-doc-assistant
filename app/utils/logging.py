import json
import logging
import sys
from datetime import datetime, timezone

# Standard LogRecord fields to exclude from the extra payload
_LOG_RECORD_FIELDS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        # Extra fields added via logger.info(..., extra={...}) land directly
        # on record.__dict__ — pull them out by excluding standard fields
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_FIELDS and not key.startswith("_"):
                log[key] = value
        return json.dumps(log)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
