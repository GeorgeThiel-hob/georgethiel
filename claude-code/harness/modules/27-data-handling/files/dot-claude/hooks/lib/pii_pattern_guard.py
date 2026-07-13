"""pii_pattern_guard.py — best-effort WARN-first PII-pattern gate.

Kit-authored, no origin-project equivalent (module `27-data-handling`'s deny-list
rules are new content, generalized from this kit's origin CLAUDE.md's "Never expose"
hard rule — see the module README's AC-6 attribution).

On a Write/Edit/MultiEdit whose destination path is shaped like a logs- or
memory-file destination, scans the post-edit content for IBAN-shaped,
card-number-shaped, and US-SSN-shaped strings. On a match, appends a WARN record to
`~/.claude/logs/pii-pattern-warns.log` and prints a stderr WARN — it NEVER blocks the
write.

Labeled explicitly best-effort: regex PII detection is imperfect. It catches strings
that are *shaped* like the patterns below; it has no notion of context, will not catch a
personal detail written out in prose, and can both false-positive (a shaped-but-harmless
string) and false-negative (a real one in an unexpected format). This is a control that
reduces exposure and makes some violations visible — it is not a guarantee that no
personal or financial data ever reaches a logged or persisted file.

Registration: this module's own `settings-fragment.json` (a dedicated `PreToolUse`
entry, matcher `Write|Edit|MultiEdit`) — see the module README's "Registration"
section for why this is not wired through `10-hooks-base`'s
`pretooluse_dispatcher.py` `_maybe_register` list the way module 20's checks are.

stdlib-only (`re`, plus `json`/`sys`/`pathlib`/`datetime` for the standalone entry
point and the shared `HookResult`/`log_hook_error` helpers from module 10's
`lib/__init__.py`).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# This file registers as its OWN standalone PreToolUse entry point (see the module
# README's "Registration" section) and so runs as `__main__`, not as a package member
# of `lib` — a relative `from . import ...` would raise "attempted relative import
# with no known parent package" in that mode. Bootstrap `.claude/hooks/` onto
# sys.path (mirrors `pretooluse_dispatcher.py`'s own self-bootstrapping) and import
# `lib` absolutely instead, so this works whether run directly or (in principle)
# imported by another script that has already done the same.
_LIB_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _LIB_DIR.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from lib import HookResult, log_hook_error  # noqa: E402

_HOOK_NAME = "check_pii_patterns"

# Warn-log path — read at CALL time (never bound at import), so a test overlay can
# redirect it without vacuously passing a no-warn assertion.
_WARN_LOG = Path.home() / ".claude" / "logs" / "pii-pattern-warns.log"

# Path-shape check: only scan content headed for something that looks like a logs or
# memory destination. Everything else is out of scope for this check.
_LOG_OR_MEMORY_SHAPE = re.compile(
    r"(^|/)(logs?|memory)(/|$)|lessons-log", re.IGNORECASE
)

# Illustrative, best-effort shape patterns — NOT a validated PII-detection library.
_IBAN_SHAPE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
_CARD_SHAPE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_SSN_SHAPE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

_PATTERNS = (
    ("IBAN-shaped", _IBAN_SHAPE),
    ("card-number-shaped", _CARD_SHAPE),
    ("SSN-shaped", _SSN_SHAPE),
)


def _content_for(tool_name: str, tool_input: dict) -> str:
    """Best-effort content extraction — the diff slice only, not a full post-edit
    reconstruction (this module has no dependency on module 23's `_post_edit_content`,
    to stay stdlib-only and independent of whether `23-guards` is installed).
    """
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return ""


def _emit_warn(file_path: str, label: str, snippet: str) -> None:
    """Append a structured JSON warn record and print a stderr WARN. Best-effort —
    never raises."""
    warn_log = _WARN_LOG  # CALL-TIME read, do not hoist
    try:
        warn_log.parent.mkdir(parents=True, exist_ok=True)
        with warn_log.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "file": file_path,
                        "pattern": label,
                        "snippet_len": len(snippet),
                    }
                )
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass
    try:
        print(
            f"PII-PATTERN WARN: {file_path} — content matches a {label} string. "
            "Best-effort regex check (may be a false positive); verify no real "
            "personal/financial data is being written to a logs/memory path. "
            "(Non-blocking; write proceeds.)",
            file=sys.stderr,
        )
    except Exception:  # noqa: BLE001
        pass


def check_pii_patterns(stdin_dict: dict) -> HookResult:
    """WARN-first PII-pattern gate. NEVER blocks — always returns allow.

    Scans Write/Edit/MultiEdit content destined for a logs- or memory-shaped path for
    IBAN/card/SSN-shaped strings. On a match, emits a WARN (log + stderr) and allows
    the write.
    """
    allow = HookResult(allow=True, block_message="")
    try:
        tool_name = stdin_dict.get("tool_name", "")
        if tool_name not in ("Write", "Edit", "MultiEdit"):
            return allow

        tool_input = stdin_dict.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if not file_path or not _LOG_OR_MEMORY_SHAPE.search(file_path):
            return allow

        content = _content_for(tool_name, tool_input)
        if not content:
            return allow

        for label, pattern in _PATTERNS:
            m = pattern.search(content)
            if m:
                _emit_warn(file_path, label, m.group(0))
        return allow
    except Exception as exc:  # noqa: BLE001 — fail open, never crash the write
        log_hook_error(_HOOK_NAME, str(exc))
        return allow


def main() -> None:
    """Standalone PreToolUse entry point (this hook registers via its own
    `settings-fragment.json`, not via `pretooluse_dispatcher.py`'s `dispatch()`).

    Fails open at every layer: stdin parse, check, and stdout write. Always exits 0
    so this hook never wedges the session.
    """
    stdin_dict: dict = {}
    try:
        stdin_dict = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        pass

    try:
        result = check_pii_patterns(stdin_dict)
        response = (
            {"decision": "allow"}
            if result.allow
            else {
                "decision": "block",
                "message": result.block_message,
            }
        )
    except Exception:  # noqa: BLE001
        response = {"decision": "allow"}

    try:
        print(json.dumps(response))
    except Exception:  # noqa: BLE001
        print('{"decision": "allow"}')

    sys.exit(0)


if __name__ == "__main__":
    main()
