"""
subagentstop_log.py — Hook 10 (best-effort): log subagent failures.

Triggered via SubagentStop. Non-blocking — always exits 0.
Appends JSON records to ~/.claude/logs/subagent-failures.log for post-session review.

Also scans Agent tool_response content for behavioral claims missing confidence
labels (Verified/Estimated/Assumed/Unknown) and appends misses to
~/.claude/logs/confidence-label-misses.log (AC-6, best-effort, non-blocking).

Additionally performs read-only seat-mismatch detection (`check_delivered_model`,
AC-10): compares the model a finished subagent was actually DELIVERED against the
seat its dispatch REQUESTED, logging a record + stderr warning on a mismatch. This
is detect-and-log ONLY — SubagentStop has no block channel, so it never blocks or
rolls back (still always exits 0). Best-effort: the delivered model is read
reliably, but the requested seat is inferred from the dispatch's `[seat:...]` tag
in the transcript's first user message and the check silently no-ops (fails SAFE)
when that tag cannot be recovered.
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
# Delivered-model seat-mismatch detection (AC-10) — detect-and-log ONLY
# ---------------------------------------------------------------------------
#
# Source-of-truth nuance (Verified — Task-1 payload captures,
# docs/superpowers/briefs/KIT-SEAT-ENFORCE-01-payload-captures.md): in THIS
# Claude Code version subagent assistant entries are NOT inlined into the
# parent `transcript_path` as isSidechain rows (0 of 2568 there). The delivered
# model id lives ONLY in the subagent's own `agent_transcript_path`
# (`message.model` on its assistant entries), which also carries the dispatch
# prompt as its first user message (where the [seat:...] tag lives). So this
# check reads `agent_transcript_path`, NOT `transcript_path`+isSidechain — the
# latter would scan the wrong transcript and silently detect nothing.


def _flatten_text(content) -> str:
    """Return the text of a transcript message's content (str or block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def _log_seat_mismatch(seat, allowed, delivered_model, delivered_alias) -> None:
    """Append a structured seat-mismatch record to the subagent log."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "branch": _get_branch(),
        "event": "seat-mismatch",
        "seat": seat,
        "allowed": list(allowed),
        "delivered_model": delivered_model,
        "delivered_alias": delivered_alias,
    }
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def check_delivered_model(stdin_dict: dict) -> None:
    """Detect-and-log delivered-model substitution (AC-10). NEVER blocks;
    always returns None. SubagentStop has no block channel, so this is
    observe-only: it reads the subagent's OWN transcript
    (`agent_transcript_path`), extracts the dispatch's seat tag from the first
    user message, resolves each assistant message's serving-model id to an
    alias (skipping the "<synthetic>" sentinel), and logs a seat-mismatch
    record + stderr warning when a delivered alias falls outside the seat's
    allow-list. Any missing field / unreadable file / absent model -> silent
    no-op (fail-open). SEAT_ROUTING_MODE does not change this — no block
    channel at SubagentStop."""
    try:
        from lib.seat_checks import (  # noqa: E402
            _SEAT_TAG_RE,
            _load_seat_table,
            _model_alias,
            _normalize_seat,
        )
    except Exception:  # noqa: BLE001 — module 20 absent, nothing to check
        return
    try:
        # Read the subagent's own transcript (NOT the parent transcript_path):
        # this version stores subagent assistant entries only here (Task-1).
        transcript_path = stdin_dict.get("agent_transcript_path", "")
        if not transcript_path:
            return  # no per-agent transcript pointer -> no check (fail-open)
        from lib.transcript_utils import load_entries  # noqa: E402

        entries = load_entries(transcript_path)
        if not entries:
            return

        seat = None
        for entry in entries:
            msg = entry.get("message") or {}
            if entry.get("type") == "user" or msg.get("role") == "user":
                m = _SEAT_TAG_RE.search(_flatten_text(msg.get("content")))
                if m:
                    seat = _normalize_seat(m.group(1))
                break
        if seat is None:
            return  # untagged transcript — PreToolUse owns tagging

        seats, err = _load_seat_table()
        if err is not None or seat not in seats:
            return
        allowed = seats[seat]

        for entry in entries:
            model = (entry.get("message") or {}).get("model")
            if not model or model == "<synthetic>":
                continue
            alias = _model_alias(str(model))
            if alias is None or alias == "<ambiguous>":
                _log_seat_mismatch(seat, allowed, str(model), "unresolved")
                print(
                    f"SEAT ROUTING: subagent for seat {seat} served "
                    f"unresolvable model {model!r} (allowed {allowed}).",
                    file=sys.stderr,
                )
                continue
            if alias not in allowed:
                _log_seat_mismatch(seat, allowed, str(model), alias)
                print(
                    f"SEAT ROUTING: subagent for seat {seat} was served "
                    f"{alias} (from {model!r}); allowed {allowed}.",
                    file=sys.stderr,
                )
    except Exception:  # noqa: BLE001 — never wedge the SubagentStop event
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
        check_delivered_model(stdin_dict)
    except Exception as exc:  # noqa: BLE001
        # Fail open — log error but do not wedge session
        error_log = Path.home() / ".claude" / "logs" / "hook-errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with error_log.open("a") as fh:
            fh.write(json.dumps({"hook": "subagentstop_log", "error": str(exc)}) + "\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
