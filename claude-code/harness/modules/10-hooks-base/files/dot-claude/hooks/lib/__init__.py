"""Shared types and helpers for .claude/hooks check functions."""

import json
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path

HookResult = namedtuple("HookResult", ["allow", "block_message"])

_ERROR_LOG = Path.home() / ".claude" / "logs" / "hook-errors.log"


def log_hook_error(hook: str, error: str) -> None:
    """Append a fail-open diagnostic line to the shared hook error log.

    Used by check functions on their internal fail-open paths so a silently
    non-functional guard still leaves a diagnosable trace. Never raises — a
    logging failure must not break the fail-open path it is documenting.
    """
    try:
        _ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _ERROR_LOG.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "hook": hook,
                        "error": error,
                    }
                )
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass
