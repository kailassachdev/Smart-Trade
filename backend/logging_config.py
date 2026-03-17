"""
logging_config.py
-----------------
Structured JSON logging using structlog.
Every log event carries: timestamp, level, event-type, and context fields
(user_id, symbol, action, etc.) for easy ingestion into log aggregators.

ARCHITECTURAL IMPROVEMENT #8: Structured Logging
"""

import logging
import structlog
import sys

def configure_logging():
    """Call this once at application startup in main.py."""

    # Configure Python's standard logging to forward to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,        # Thread-local context (e.g., request_id)
            structlog.stdlib.add_log_level,                 # Add 'level' field
            structlog.stdlib.add_logger_name,               # Add 'logger' field
            structlog.processors.TimeStamper(fmt="iso"),    # ISO-8601 timestamp
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer()                  # Pretty-print for dev; swap for JSONRenderer in prod
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

# ── Pre-defined event-type constants ──────────────────────────────────────────
# Use these as the `event` argument so log queries are predictable.

AGENT_DECISION    = "AGENT_DECISION"
TRADE_EXECUTED    = "TRADE_EXECUTED"
TRADE_SKIPPED     = "TRADE_SKIPPED"
RISK_BLOCKED      = "RISK_BLOCKED"
WALLET_UPDATE     = "WALLET_UPDATE"
USER_AUTH         = "USER_AUTH"
SCHEDULER_TICK    = "SCHEDULER_TICK"
MARKET_STATUS     = "MARKET_STATUS"

# ── Get a bound logger for any module ─────────────────────────────────────────
def get_logger(name: str = __name__):
    return structlog.get_logger(name)
