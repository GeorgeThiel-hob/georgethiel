"""
seat_checks.py — Seat->model routing enforcement (KIT-SEAT-ENFORCE-01).

check_seat_routing(stdin_dict) -> HookResult validates every Task/Agent
dispatch against the installed .claude/state/seat-table.json:
  - a `model` param is present (AC-2),
  - a [seat:<name>] tag leads the dispatch prompt / description (AC-3),
  - the requested model is in the declared seat's allow-list, BOTH
    over- and under-modeled directions blocked (AC-3),
  - a valid tag + allowed model passes with zero output (AC-4).

Fail-open on its own errors; missing/corrupt seat table -> WARN once + allow
(AC-5). Block is the default; SEAT_ROUTING_MODE=warn downgrades every
violation to allow-with-stderr-warning. Pure Python, no shell-outs (I4).
"""

import json
import os
import re
import sys
from pathlib import Path

from . import HookResult, log_hook_error

# .claude/hooks/lib/../../.. = project root
_REPO_ROOT: Path = Path(__file__).parents[3]
_SEAT_TABLE_PATH: Path = _REPO_ROOT / ".claude" / "state" / "seat-table.json"
_WARN_MARKER: Path = _REPO_ROOT / ".claude" / "state" / ".seat-table-warn-emitted"

# Case-insensitive; tolerant of whitespace after the colon and around the name.
_SEAT_TAG_RE = re.compile(r"\[seat:\s*([a-z_ -]+?)\s*\]", re.IGNORECASE)

# Known model-alias tokens; a model string resolves by containment.
_ALIAS_TOKENS = ("haiku", "sonnet", "opus", "fable")

# A prompt tag whose regex match STARTS at index < _WINDOW counts as in-window.
# Description tags count at any position.
_WINDOW = 500

# Seat name -> module that must be installed for the seat row to appear.
CONDITIONAL_SEATS = {"persona": "31-debate-tools"}


def _model_alias(value):
    """Map a model string to one alias token by containment, or None if no
    known token matches. Returns "<ambiguous>" when >=2 DISTINCT tokens are
    present (two-token rule: fail loud, never silently pick a precedence)."""
    low = value.lower()
    hits = [tok for tok in _ALIAS_TOKENS if tok in low]
    if not hits:
        return None
    if len(set(hits)) >= 2:
        return "<ambiguous>"
    return hits[0]


def _normalize_seat(name):
    """Lowercase; hyphens and spaces -> underscore."""
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _extract_seat_tags(prompt, description):
    """Return (names, late_only).

    names: distinct normalized seat names from `description` (any position)
    UNION `prompt` matches whose start index < _WINDOW. Regex runs over the
    FULL prompt then filters by start index — never slice-then-regex (which
    would truncate a tag straddling the boundary).
    late_only: True when names is empty, the prompt regex DID match, but every
    match started at/after _WINDOW (a present-but-late tag)."""
    names = set()
    for m in _SEAT_TAG_RE.finditer(description):
        names.add(_normalize_seat(m.group(1)))
    prompt_total = 0
    prompt_in_window = 0
    for m in _SEAT_TAG_RE.finditer(prompt):
        prompt_total += 1
        if m.start() < _WINDOW:
            names.add(_normalize_seat(m.group(1)))
            prompt_in_window += 1
    late_only = (not names) and prompt_total > 0 and prompt_in_window == 0
    return names, late_only


def _load_seat_table():
    """Return (seats_dict, error). error is 'missing' | 'corrupt' | None."""
    try:
        raw = _SEAT_TABLE_PATH.read_text(encoding="utf-8")
    except OSError:
        return None, "missing"
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None, "corrupt"
    seats = data.get("seats")
    if not isinstance(seats, dict):
        return None, "corrupt"
    return seats, None


def _warn_once(message):
    """Emit a stderr warning once per install; suppress repeats via a marker."""
    try:
        if _WARN_MARKER.exists():
            return
        _WARN_MARKER.parent.mkdir(parents=True, exist_ok=True)
        _WARN_MARKER.write_text("", encoding="utf-8")
    except OSError:
        pass
    print(message, file=sys.stderr)


def _result(mode, message):
    """block mode -> block; warn mode -> allow + stderr warning."""
    if mode == "warn":
        print(f"SEAT ROUTING (warn): {message}", file=sys.stderr)
        return HookResult(allow=True, block_message=None)
    return HookResult(allow=False, block_message=message)


def check_seat_routing(stdin_dict):
    """PreToolUse seat->model routing check. Pure function, fail-open."""
    try:
        mode = os.environ.get("SEAT_ROUTING_MODE", "block")
        if mode != "warn":
            mode = "block"

        seats, err = _load_seat_table()
        if err is not None:
            _warn_once(
                f"SEAT ROUTING: seat-table.json {err} at {_SEAT_TABLE_PATH} — "
                "routing checks disabled until re-install; allowing dispatch."
            )
            return HookResult(allow=True, block_message=None)

        valid = ", ".join(sorted(seats))
        tool_input = stdin_dict.get("tool_input", {}) or {}
        prompt = tool_input.get("prompt", "") or ""
        description = tool_input.get("description", "") or ""

        # AC-2: model param present.
        model = tool_input.get("model")
        if not model:
            return _result(
                mode,
                "seat routing: dispatch has no `model` param — add "
                'model: "haiku"|"sonnet"|"opus" to the dispatch (it would '
                "otherwise silently inherit the orchestrator's model).",
            )

        # AC-3: seat tag present, in the leading window, exactly one, known.
        names, late_only = _extract_seat_tags(prompt, description)
        if late_only:
            return _result(
                mode,
                "seat routing: seat tag found beyond the first 500 characters "
                "— move it to the prompt lead or `description`.",
            )
        if not names:
            return _result(
                mode,
                "seat routing: dispatch declares no seat — lead the prompt (or "
                f"the description) with a seat tag. Valid seats: {valid}.",
            )
        if len(names) >= 2:
            return _result(
                mode,
                "seat routing: multiple seat tags in the leading window — keep "
                f"exactly one. Found: {', '.join(sorted(names))}.",
            )
        seat = next(iter(names))
        if seat not in seats:
            hint = ""
            if seat in CONDITIONAL_SEATS:
                hint = (
                    f" — seat {seat} requires module {CONDITIONAL_SEATS[seat]} "
                    "(re-install after adding it)"
                )
            return _result(
                mode,
                f"seat routing: unknown seat {seat}{hint}. Valid seats: {valid}.",
            )

        # AC-3: both-direction model validation.
        allowed = seats[seat]
        alias = _model_alias(str(model))
        if alias is None or alias == "<ambiguous>":
            return _result(
                mode,
                f"seat routing: cannot resolve model {model!r} to a known alias "
                f"({'|'.join(_ALIAS_TOKENS)}); seat {seat} allows "
                f"{', '.join(allowed)}.",
            )
        if alias not in allowed:
            return _result(
                mode,
                f"seat routing: seat {seat} allows {', '.join(allowed)}, but the "
                f"dispatch requests {alias} (from {model!r}).",
            )

        # AC-4: valid tag + allowed model -> allow, zero output.
        return HookResult(allow=True, block_message=None)
    except Exception as exc:  # noqa: BLE001 — fail open
        log_hook_error("seat_checks", exc)
        return HookResult(allow=True, block_message=None)
