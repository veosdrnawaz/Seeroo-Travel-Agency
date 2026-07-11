"""
logging_config.py
─────────────────
Configures application-wide structured logging.

Development mode : coloured human-readable text output.
Production mode  : machine-readable JSON Lines output (one JSON object per line).

JSON log schema (production):
  {
    "timestamp": "2026-07-11T19:00:00.000Z",   # ISO-8601 UTC
    "level":     "INFO",
    "logger":    "seeroo_chat_route",
    "message":   "...",
    "route":     "/api/v1/chat",               # optional
    "thread_id": "abc-123",                    # optional
    "booking_id": "b1c2d3",                    # optional
    "error":     "...",                        # optional
    "exc_info":  "Traceback ..."               # optional, on exceptions
  }

Usage:
  from app.core.logging_config import setup_logging
  setup_logging()   # called once in main.py before anything else
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """
    Emits each log record as a single-line JSON object.
    Extra context fields (route, thread_id, booking_id, error) are merged
    from the `extra` dict passed to logger.info/warning/error calls.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
                         .strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }

        # Merge optional structured context fields
        for field in ("route", "thread_id", "booking_id", "error"):
            val = getattr(record, field, None)
            if val is not None:
                log_obj[field] = val

        # Append exception traceback if present
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_obj["exc_info"] = record.exc_text

        return json.dumps(log_obj, ensure_ascii=False)


class _DevFormatter(logging.Formatter):
    """
    Human-readable coloured formatter for development terminals.
    Format: [HH:MM:SS] LEVEL     logger_name: message
    """
    COLOURS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self.COLOURS.get(record.levelname, "")
        time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level_str = f"{colour}{record.levelname:<8}{self.RESET}"
        base = f"[{time_str}] {level_str} {record.name}: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging(json_output: bool = False, level: str = "INFO") -> None:
    """
    Configure root logger with the appropriate formatter.

    Args:
        json_output: True → JSON Lines (production); False → coloured dev format.
        level:       Logging level string, e.g. "INFO", "WARNING", "DEBUG".
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)

    if json_output:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(_DevFormatter())

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Clear any existing handlers (avoid duplicates on reloads)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "openai", "chromadb", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("seeroo_backend").info(
        f"Logging initialised — mode={'json' if json_output else 'dev'} level={level}"
    )
