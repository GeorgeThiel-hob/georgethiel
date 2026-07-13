"""stop_citation_guard.py — main-thread Stop hook.

Blocks an uncited load-bearing claim about code/data state in the orchestrator's
final assistant turn. Fail-open absolute (any error -> exit 0). 3-loop bounded
guard, count DERIVED from the transcript (no mutable counter file).

Text extraction: PREFERS data["last_assistant_message"] (verified in-env to be the
model's full, clean, concatenated final message as a plain string). Falls back to
transcript-tail parse when absent or empty.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import IO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.claim_detector import (  # noqa: E402
    Finding,
    scan_for_quantifier_claims,
    scan_for_uncited_claims,
)
from lib.transcript_utils import load_entries  # noqa: E402

MAX_REBLOCKS = 3
# Block a turn only when it carries >= this many DISTINCT flagged lines (owner decision).
# A single stray flag (e.g. one process-narration 'because') is logged but does not block;
# the block fires on claim-DENSE unsourced turns where errors cluster. Tunable knob — env
# override CITATION_GUARD_MIN_FLAGS lets the owner retune on live data without an edit.
MIN_FLAGS_TO_BLOCK = int(os.environ.get("CITATION_GUARD_MIN_FLAGS", "2"))
_MODE = os.environ.get("CITATION_GUARD_MODE", "block")  # 'block' | 'log'
_MISSES_LOG = Path.home() / ".claude" / "logs" / "citation-guard-misses.log"
_CMD_WRAPPER = re.compile(r"^\s*<(?:local-)?command-")
# Host marker prepended to a Stop-hook block→continue (verified in-env:
# type=user, isMeta=True, content str begins with this). One per block.
_STOP_FEEDBACK_PREFIX = "Stop hook feedback"

# ---------------------------------------------------------------------------
# Graduated block-reason text
# ---------------------------------------------------------------------------

_LOOP_TEXT = {
    1: (
        "A claim about code/data state isn't grounded — add the citation "
        "(file:line / value / query result) or revise it."
    ),
    2: (
        "Still ungrounded after a revision — re-open the source and confirm; "
        "do not re-state the same framing."
    ),
    3: (
        "Third pass. If you can't ground this, flag it Unknown/Assumed and say "
        "what you'd need to verify — do not ship it as fact."
    ),
}

_CLASS_LOOKUP = {
    "coefficient-vs-intuition": (
        "trace the cause to a fitted coefficient / file:line, not an output-pattern story"
    ),
    "staleness": (
        "confirm the cited result's param-config AND snapshot-date match current state"
    ),
    "snapshot-vs-permanent": (
        "static read of a time-varying quantity? cite its rate of change"
    ),
    "already-implemented": "grep first — does the code already do this?",
    "inferred-dependency": "a code path is not an inherent dependency — verify it",
}

# ---------------------------------------------------------------------------
# Transcript helpers
# ---------------------------------------------------------------------------


def extract_final_assistant_text(entries: list[dict]) -> str:
    """Concat all text blocks of the FINAL assistant message.

    Scans tail for the last entry with type=='assistant' AND stop_reason=='end_turn',
    then collects all entries sharing that message.id and concatenates their text blocks.
    Discriminator is type/stop_reason, NOT role.
    """
    final_id: str | None = None
    for e in reversed(entries):
        if (
            e.get("type") == "assistant"
            and e.get("message", {}).get("stop_reason") == "end_turn"
        ):
            final_id = e.get("message", {}).get("id")
            break

    if final_id is not None:
        group = [
            e
            for e in entries
            if e.get("type") == "assistant"
            and e.get("message", {}).get("id") == final_id
        ]
    else:
        # No end_turn found → take the last contiguous assistant run (interrupted turn)
        group = []
        for e in reversed(entries):
            if e.get("type") == "assistant":
                group.append(e)
            elif group:
                break
        group.reverse()

    texts: list[str] = []
    for e in group:
        for block in e.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
    return "\n".join(texts)


def get_text_to_scan(data: dict, entries: list[dict]) -> str:
    """Return the text to scan for claims.

    PREFERS data["last_assistant_message"] (verified in-env to be the full, clean,
    concatenated final message as a plain string). Falls back to transcript extraction
    when absent or empty-after-strip. This removes a silent-no-op risk from
    the text path.
    """
    lam = data.get("last_assistant_message", "")
    if isinstance(lam, str) and lam.strip():
        return lam
    return extract_final_assistant_text(entries)


# ---------------------------------------------------------------------------
# Genuine-prompt discriminator
# ---------------------------------------------------------------------------


def is_genuine_prompt(entry: dict) -> bool:
    """A real human prompt, NOT a tool_result / meta / command wrapper.

    A naive 'non-meta user entry' check resets on tool_results
    (which vastly outnumber real prompts) and silently defeats the guard.
    """
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return not _CMD_WRAPPER.match(content)
    if isinstance(content, list):
        text_blocks = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        has_tool_result = any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        )
        # Re-check the command wrapper on list-form text too — a slash-command
        # delivered as a list-with-text-block must not be treated as a genuine prompt (ladder reset).
        joined = " ".join(text_blocks).lstrip()
        return (
            bool(text_blocks) and not has_tool_result and not _CMD_WRAPPER.match(joined)
        )
    return False


# ---------------------------------------------------------------------------
# Prior block count
# ---------------------------------------------------------------------------


def _is_stop_block_injection(entry: dict) -> bool:
    """A host-injected Stop-hook block→continue marker — exactly one per PRIOR block.

    Verified in-env: type=='user', isMeta truthy, content is a str (or text block)
    beginning with 'Stop hook feedback'. This counts blocks DIRECTLY, independent
    of message-id / entry-pairing behavior — the assumption-free signal.
    """
    if entry.get("type") != "user" or not entry.get("isMeta"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return content.lstrip().startswith(_STOP_FEEDBACK_PREFIX)
    if isinstance(content, list):
        for b in content:
            if (
                isinstance(b, dict)
                and b.get("type") == "text"
                and b.get("text", "").lstrip().startswith(_STOP_FEEDBACK_PREFIX)
            ):
                return True
    return False


def prior_block_count(entries: list[dict]) -> int:
    """Number of prior Stop blocks in this chain since the last genuine prompt.

    Two INDEPENDENT signals, combined with max() so a wedge needs BOTH to fail at once
    (belt-and-suspenders; confirmed via second-opinion review). At every hook-fire moment
    both equal the true prior-block count; they diverge only under a host-behavior
    anomaly, and max() always picks the larger → the count can only climb FASTER, never
    stall → no wedge:

    1. DISTINCT completed (end_turn) TURNS by message.id, minus 1. A completed turn is
       recorded as MULTIPLE consecutive entries sharing ONE message.id, each
       stop_reason=='end_turn' (verified in-env: every window raw end_turn entries=2,
       distinct ids=1) — so counting raw entries would double-count and halve the budget.
       A block→continue gets a FRESH message.id (verified in-env: a fresh id on the
       continuation entry vs. the blocked one), so the distinct count advances per block.
       Missing id → object identity (fail-early).
       WEDGE MODE (mitigated): if a future host ever REUSED the blocked turn's id, distinct
       would stall at 1 → 0 prior → never reach the ceiling. Signal 2 rescues this.
    2. Direct count of 'Stop hook feedback' host injections (one per prior block) since the
       last genuine prompt — assumption-free re: ids/pairing.
       WEDGE MODE (mitigated): if the host injection wording ever changed, this returns 0.
       Signal 1 rescues this.

    Derived purely from the transcript → no mutable counter (dissolves a counter-based
    concurrency/reset class of bug).
    A genuine prompt resets both (loop stops at the genuine-prompt boundary).
    """
    seen_turns: set = set()
    injections = 0
    for e in reversed(entries):
        if is_genuine_prompt(e):
            break
        if _is_stop_block_injection(e):
            injections += 1
            continue
        if (
            e.get("type") == "assistant"
            and e.get("message", {}).get("stop_reason") == "end_turn"
        ):
            mid = e.get("message", {}).get("id")
            seen_turns.add(mid if mid else id(e))
    return max(max(0, len(seen_turns) - 1), injections)


# ---------------------------------------------------------------------------
# Block reason builder
# ---------------------------------------------------------------------------


def build_reason(findings: list[Finding], loop: int) -> str:
    """Graduated reason text: loop-indexed preamble + triggered classes only."""
    classes = sorted(
        {f.blindspot_class for f in findings}
    )  # triggered classes only
    lines = [_LOOP_TEXT.get(loop, _LOOP_TEXT[3])]
    lines += [f"  [{c}] {_CLASS_LOOKUP.get(c, c)}" for c in classes]
    lines.append("  Offending: " + " | ".join(f.line for f in findings[:3]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def _log(findings: list[Finding]) -> None:
    try:
        _MISSES_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _MISSES_LOG.open("a") as fh:
            for f in findings:
                fh.write(f"{f.blindspot_class}\t{f.line}\n")
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(stdin: IO[str] | None = None) -> None:
    """Main hook handler. Fail-open: any exception → exit 0, no partial block on stdout."""
    try:
        data = json.load(stdin if stdin is not None else sys.stdin)

        # Load entries from transcript (needed for count + fallback text)
        transcript_path = data.get("transcript_path", "")
        try:
            entries = load_entries(transcript_path) if transcript_path else []
        except Exception:  # noqa: BLE001
            entries = []

        # Determine text to scan (prefer last_assistant_message, fall back to transcript)
        text = get_text_to_scan(data, entries)
        if not text:
            return  # nothing to scan → clean pass

        # Detect findings
        findings = scan_for_uncited_claims(text) + scan_for_quantifier_claims(text)
        if not findings:
            return  # clean pass → exit 0

        # Always log findings (even in log mode, and even below the block threshold)
        _log(findings)

        if _MODE != "block":
            return  # log-only mode

        # Block threshold: only claim-DENSE turns (>= MIN_FLAGS_TO_BLOCK distinct lines)
        # block; a lone stray flag is logged-not-blocked. Findings already logged above.
        if len({f.line for f in findings}) < MIN_FLAGS_TO_BLOCK:
            return  # below threshold → logged, not blocked

        # Transcript-derived loop count (not from last_assistant_message)
        prior = prior_block_count(entries)
        if prior >= MAX_REBLOCKS:
            print(
                "⚠ citation gate hit ceiling (3x) — claim shipped ungrounded, flagged for review",
                file=sys.stderr,
            )
            return  # ceiling release → exit 0, no block

        # Increment-then-emit: compute reason based on (prior + 1) loop number
        reason = build_reason(findings, prior + 1)
        decision = {
            "decision": "block",
            "reason": reason,
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": reason,
            },
        }
        # Single, LAST print statement — any earlier throw fails open
        print(json.dumps(decision))

    except Exception as exc:  # noqa: BLE001
        # Log the error but NEVER block (fail-open absolute)
        try:
            err = Path.home() / ".claude" / "logs" / "hook-errors.log"
            err.parent.mkdir(parents=True, exist_ok=True)
            with err.open("a") as fh:
                fh.write(
                    json.dumps({"hook": "stop_citation_guard", "error": str(exc)})
                    + "\n"
                )
        except Exception:  # noqa: BLE001
            pass
        # Fail OPEN: no block emitted, exit 0


if __name__ == "__main__":
    main()
    sys.exit(0)
