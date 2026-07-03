import json
import logging
import time
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit structured JSON log lines for observability pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id") and record.request_id:
            payload["request_id"] = record.request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("job_id", "task_name", "duration_ms", "metric"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(*, level: str = "INFO", log_format: str = "json") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    if log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))

    root.addHandler(handler)


class LogContext:
    """Attach request/job context to log records via LoggerAdapter."""

    def __init__(self, logger: logging.Logger, **context: Any):
        self._logger = logging.LoggerAdapter(logger, context)

    def info(self, msg: str, **extra: Any) -> None:
        self._logger.info(msg, extra=extra)

    def warning(self, msg: str, **extra: Any) -> None:
        self._logger.warning(msg, extra=extra)

    def error(self, msg: str, **extra: Any) -> None:
        self._logger.error(msg, extra=extra)


def log_duration(logger: logging.Logger, operation: str, started: float, **extra: Any) -> None:
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "%s completed",
        operation,
        extra={"duration_ms": duration_ms, "metric": operation, **extra},
    )
