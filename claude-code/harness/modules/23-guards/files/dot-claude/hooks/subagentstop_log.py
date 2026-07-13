"""
subagentstop_log.py — Hook 10 (best-effort): log subagent failures.

Triggered via SubagentStop. Non-blocking — always exits 0.
Appends JSON records to ~/.claude/logs/subagent-failures.log for post-session review.

Also scans Agent tool_response content for behavioral claims missing confidence
labels (Verified/Estimated/Assumed/Unknown) and appends misses to
~/.claude/logs/confidence-label-misses.log (AC-6, best-effort, non-blocking).
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import IO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.claim_detector import scan_for_unlabeled_claims  # noqa: E402

_LOG_DIR = Path.home() / ".claude" / "logs"
_LOG_PATH = _LOG_DIR / "subagent-failures.log"

_FAILURE_MARKERS = {
    "output cap": "output cap",
    "context overflow": "context overflow",
    "scope explosion": "scope explosion",
}


def _is_failure(exit_code: int, output: str) -> tuple[bool, str]:
    """Return (is_failure, reason). reason is '' if not a failure."""
    output_lower = output.lower()
    for marker, label in _FAILURE_MARKERS.items():
        if marker in output_lower:
            return True, label
    if exit_code != 0:
        return True, f"exit_code:{exit_code}"
    return False, ""


def _get_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            check=True,
        )
        return result.stdout.decode().strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def log_subagent_result(stdin_dict: dict) -> None:
    """Main logic — log failure if applicable. Pure side-effecting function."""
    exit_code: int = stdin_dict.get("exit_code", 0)
    output: str = stdin_dict.get("output", "")

    is_fail, reason = _is_failure(exit_code, output)
    if not is_fail:
        return

    # Build prompt hash from subagent output (first 1000 chars)
    prompt_sample = output[:1000]
    prompt_hash = hashlib.sha256(prompt_sample.encode()).hexdigest()[:16]

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "branch": _get_branch(),
        "reason": reason,
        "prompt_hash": prompt_hash,
    }

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Confidence-label scanner (AC-6) — best-effort, non-blocking
# ---------------------------------------------------------------------------

_LABEL_MISSES_LOG = Path.home() / ".claude" / "logs" / "confidence-label-misses.log"


def _append_label_misses(misses: list[str], agent_type: str, branch: str) -> None:
    """Append unlabeled-claim lines to the confidence-label-misses log."""
    log_dir = Path.home() / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / "confidence-label-misses.log"
    ts = datetime.now(timezone.utc).isoformat()
    with log.open("a") as fh:
        for miss in misses:
            fh.write(f"{ts}\t{agent_type}\t{branch}\t{miss}\n")


def maybe_log_label_misses(stdin_dict: dict) -> None:
    """Scan Agent tool_response for unlabeled behavioral claims (best-effort)."""
    try:
        text_parts: list[str] = []
        for block in stdin_dict.get("tool_response", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        if not text_parts:
            return
        text = "\n".join(text_parts)
        misses = scan_for_unlabeled_claims(text)
        if not misses:
            return
        agent_type: str = stdin_dict.get("tool_input", {}).get("subagent_type", "?")
        try:
            branch = (
                subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                ).stdout.strip()
                or "?"
            )
        except Exception:  # noqa: BLE001
            branch = "?"
        _append_label_misses(misses, agent_type, branch)
    except Exception:  # noqa: BLE001
        # Never block the SubagentStop event
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(stdin: IO[str] | None = None) -> None:
    """Entry point for SubagentStop hook.

    Parameters
    ----------
    stdin:
        File-like object to read JSON from. Defaults to ``sys.stdin``.
        Accepted as a keyword argument so tests can pass ``StringIO`` objects
        without touching ``sys.stdin``.

    Always returns normally (never raises). When invoked via ``__main__``
    the caller issues ``sys.exit(0)`` to satisfy the hook contract.
    """
    try:
        source = stdin if stdin is not None else sys.stdin
        stdin_dict = json.load(source)
        log_subagent_result(stdin_dict)
        maybe_log_label_misses(stdin_dict)
    except Exception as exc:  # noqa: BLE001
        # Fail open — log error but do not wedge session
        error_log = Path.home() / ".claude" / "logs" / "hook-errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with error_log.open("a") as fh:
            fh.write(json.dumps({"hook": "subagentstop_log", "error": str(exc)}) + "\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
