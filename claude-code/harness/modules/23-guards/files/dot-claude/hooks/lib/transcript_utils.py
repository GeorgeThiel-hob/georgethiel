"""
transcript_utils.py — shared helpers for reading Claude Code session transcripts.

Provides:
  load_entries(transcript_path) -> list[dict]
  advisor_call_ids(transcript_path) -> set[str]
  has_advisor_call(transcript_path) -> bool

advisor() is a server-side Claude API tool (non-hookable), but every real call
writes a harness-authored ``server_tool_use`` block with ``name == "advisor"``
into the session transcript JSONL. The model cannot emit that block by typing,
so its presence is forge-resistant evidence the call occurred.
"""

import json
from collections import namedtuple

AdvisorCall = namedtuple("AdvisorCall", ["id", "session_id", "git_branch", "timestamp"])


def load_entries(transcript_path: str) -> list[dict]:
    """Parse the JSONL transcript; skip blank/malformed lines. [] on OSError."""
    entries: list[dict] = []
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entries.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def advisor_calls(transcript_path: str) -> list[AdvisorCall]:
    """One AdvisorCall per real advisor() invocation, carrying its binding fields.

    `id` comes from the server_tool_use BLOCK; `session_id`/`git_branch`/`timestamp`
    are read from the TOP-LEVEL entry (siblings of `message`). Blocks with a falsy id
    are skipped (mirrors advisor_call_ids). Non-dict entries and non-str binding
    fields are guarded/coerced so a malformed transcript never crashes a caller on
    the fail-closed /GIT path.
    """
    calls: list[AdvisorCall] = []
    for entry in load_entries(transcript_path):
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        git_branch = entry.get("gitBranch")
        if not isinstance(git_branch, str):
            git_branch = None
        session_id = entry.get("sessionId")
        if not isinstance(session_id, str):
            session_id = None
        timestamp = entry.get("timestamp")
        if not isinstance(timestamp, str):
            timestamp = None
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "server_tool_use"
                and block.get("name") == "advisor"
            ):
                bid = block.get("id")
                if bid:
                    calls.append(
                        AdvisorCall(
                            id=bid,
                            session_id=session_id,
                            git_branch=git_branch,
                            timestamp=timestamp,
                        )
                    )
    return calls


def advisor_call_ids(transcript_path: str) -> set[str]:
    """Return ids of real advisor() invocations (server_tool_use, name=='advisor').

    Counts the invocation block only (not the paired advisor_tool_result).
    Mere text mentions of "advisor" are ignored. Robust to a missing file
    (returns an empty set via load_entries).
    """
    return {c.id for c in advisor_calls(transcript_path)}


_SCAN_LINE_CEILING = 200_000
# Defensive: a pathological transcript degrades to False (never blocks a
# tool call) instead of scanning unbounded lines (AC-11(a)).


def has_advisor_call(transcript_path: str) -> bool:
    """Streaming early-exit check: True iff the transcript contains >=1 real
    advisor() call (server_tool_use, name=='advisor', truthy id).

    MUST NOT call load_entries — that materializes the WHOLE file into a
    list, defeating early-exit (the recorder runs on every Bash of every
    session; a 52MB transcript must not be fully parsed per call). Reads
    line-by-line and returns on the FIRST matching block, so a transcript
    whose only advisor call is near the start is cheap to check regardless
    of total size.

    Predicate- AND structurally-equivalent to advisor_calls/advisor_call_ids
    (same server_tool_use + name=="advisor" + truthy-id predicate, same
    entry["message"]["content"][] nesting and isinstance guards as
    advisor_calls above) — a divergence here would desync the record-gate
    from the count-gate.

    False on a missing/unreadable file (OSError), no match, or once
    _SCAN_LINE_CEILING lines have been scanned without a match (defensive
    ceiling; degrades to the Stop-only path, never blocks a tool call).
    """
    try:
        with open(transcript_path, encoding="utf-8") as fh:
            for i, raw in enumerate(fh):
                if i >= _SCAN_LINE_CEILING:
                    return False
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                msg = entry.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if (
                        isinstance(block, dict)
                        and block.get("type") == "server_tool_use"
                        and block.get("name") == "advisor"
                        and block.get("id")
                    ):
                        return True
    except OSError:
        return False
    return False
