import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.configuration.environment import LOG_LEVEL, APPLICATION_NAME


class JsonFormatter(logging.Formatter):
  """Custom JSON formatter for logging."""

  def format(self, record: logging.LogRecord) -> str:
    log_data: Dict[str, Any] = {
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
      "module": record.module,
      "function": record.funcName,
      "line": record.lineno,
    }

    # Add exception info if present
    if record.exc_info and record.exc_info[0]:
      log_data["exception"] = {
        "type": record.exc_info[0].__name__,
        "message": str(record.exc_info[1]),
        "traceback": self.formatException(record.exc_info),
      }

    # Add extra fields if present
    if hasattr(record, "extra_fields"):
      log_data.update(record.extra_fields)

    return json.dumps(log_data)


def get_logger(name: Optional[str] = None, level: str = LOG_LEVEL) -> logging.Logger:
  """
  Get a configured logger with JSON formatting.

  Args:
      name (str): Name of the logger (defaults to APPLICATION_NAME if None)
      level (str): Logging level (default: LOG_LEVEL)

  Returns:
      logging.Logger: Configured logger instance
  """
  if name is None:
    name = APPLICATION_NAME

  logger = logging.getLogger(name)
  logger.setLevel(level)

  # Check if the logger already has handlers configured
  if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

  return logger
