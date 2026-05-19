"""
Logger
------
Structured logging for all agent events.
Automatically masks PII before writing to logs.
"""

import logging


def _mask(text: str) -> str:
    try:
        from utils.guardrails import mask_pii
        return mask_pii(str(text))
    except Exception:
        return str(text)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("job_assistant")


def log_event(agent: str, message: str):
    """Log an agent event with PII masking."""
    safe_message = _mask(message)
    logger.info(f"[{agent.upper()}] {safe_message}")
