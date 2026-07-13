"""circularity_guard.py — circularity-rejection WARN gate.

On a MAP-dossier Write/Edit/MultiEdit, WARNS (non-blocking)
when a structured `Verified-correct` Effect-Map node's `ev:` slot cites a prior dossier
(the canonical `map-dossier.md` filename) instead of a primary source — the
circular-MAP fabrication class (a real incident where a fabricated claim compounded
through a chain of prior dossiers). WARN-first (owner decision): the guard
NEVER blocks; it appends a structured line to ~/.claude/logs/circularity-warns.log + prints
a stderr WARN, and the write proceeds. The warn log is the measurement dataset that gates a
later promotion to BLOCK.

stdlib-only (runs under run_python.sh = system python3, outside .venv).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from . import HookResult, log_hook_error
from .post_edit import _post_edit_content

# This file is .claude/hooks/lib/circularity_guard.py → parents[3] == project root.
_REPO_ROOT: Path = Path(__file__).parents[3]

_HOOK_NAME = "check_circular_evidence"

# Warn-log path — read at CALL time (like lib._ERROR_LOG), NEVER bound at import,
# so the test overlay can redirect it (else no-warn assertions pass vacuously).
_WARN_LOG: Path = Path.home() / ".claude" / "logs" / "circularity-warns.log"

# The canonical dossier basename — the signal; appears in no legitimate primary source.
_DOSSIER_BASENAME = "map-dossier.md"

# Tree-drawing connectors that mark a structured Effect-Map node line.
_TREE_CONNECTORS = ("├", "└", "│")  # ├ └ │

_STATE_TAG = "[Verified-correct"


def _is_node_line(line: str) -> bool:
    """True iff `line` is a structured Effect-Map node: first non-whitespace char is a
    tree connector AND the line carries the `[Verified-correct` state tag. Prose,
    list-bullets, and inline-code mentions (no leading connector) are NOT nodes."""
    stripped = line.lstrip()
    if not stripped:
        return False
    return stripped[0] in _TREE_CONNECTORS and _STATE_TAG in line


def _extract_ev_slot(line: str) -> Optional[str]:
    """Return the `ev:` slot: everything after the FIRST `ev:` marker that occurs AFTER
    the state-tag's closing `]`. None if there is no such slot (keying after `]` skips
    any `ev:` inside the tag; keying on the FIRST post-`]` `ev:` avoids a trailing aside
    mis-extracting the slot)."""
    tag_idx = line.find(_STATE_TAG)
    if tag_idx == -1:
        return None
    close_idx = line.find("]", tag_idx)
    if close_idx == -1:
        return None
    ev_idx = line.find("ev:", close_idx)
    if ev_idx == -1:
        return None
    return line[ev_idx + 3 :]


def _is_path_continuation(ch: str) -> bool:
    """True iff `ch` continues a path segment name: '/', ASCII alnum, '-', or '_'."""
    return ch == "/" or ch == "-" or ch == "_" or (ch.isascii() and ch.isalnum())


def _is_dossier_citation(token: str) -> bool:
    """True iff `token` contains `map-dossier.md` as a bounded path segment:
    (a) preceded by '/' or token start, AND (b) followed by token end or a
    non-path-continuation char. Scans ALL occurrences left-to-right — O(n), no
    regex, no backtracking."""
    needle = _DOSSIER_BASENAME
    start = 0
    while True:
        idx = token.find(needle, start)
        if idx == -1:
            return False
        left_ok = idx == 0 or token[idx - 1] == "/"
        after = idx + len(needle)
        right_ok = after == len(token) or not _is_path_continuation(token[after])
        if left_ok and right_ok:
            return True
        start = idx + 1


def _iter_circular_nodes(content: str) -> Iterator[tuple[int, str, str]]:
    """Yield (lineno, node_line_stripped, ev_token) for each structured Verified-correct
    node whose `ev:` slot holds a repo-confined `/`-bearing dossier-citation token.
    1-indexed lineno. `..`/absolute tokens are rejected (unverifiable → skipped + logged,
    an accepted FN). A node-line carrying the tag but with no closing `]` is malformed →
    skipped + logged (AC-7). No filesystem stat is used for the citation decision; the only
    FS op is the escape-confinement check (resolve() does not require the target to exist).
    """
    root = _REPO_ROOT.resolve()
    for i, line in enumerate(content.splitlines(), start=1):
        if not _is_node_line(line):
            continue
        tag_idx = line.find(_STATE_TAG)
        if (
            line.find("]", tag_idx) == -1
        ):  # malformed node (tag, no closing ']') → fail-open + log
            log_hook_error(
                _HOOK_NAME,
                f"line {i}: [Verified-correct node with no closing ']'; fail-open (no warn)",
            )
            continue
        ev = _extract_ev_slot(line)
        if (
            ev is None
        ):  # well-formed node, no post-] ev: slot — normal (no evidence to check)
            continue
        for tok in ev.split():
            if "/" not in tok:
                continue
            try:
                (root / tok).resolve().relative_to(
                    root
                )  # escape check (..-rel/abs → skip)
            except (ValueError, OSError):
                log_hook_error(
                    _HOOK_NAME,
                    f"line {i}: ev: token escapes repo ({tok}); fail-open (no warn)",
                )
                continue
            if _is_dossier_citation(tok):
                yield i, line.strip(), tok
                break


def _emit_warn(file_path: str, lineno: int, node_line: str, ev_token: str) -> None:
    """Append a structured JSON warn record to _WARN_LOG (dereferenced at CALL time so a
    test overlay can redirect it) and print a stderr WARN. Best-effort — never raises.
    """
    warn_log = (
        _WARN_LOG  # CALL-TIME read — do NOT hoist to a default arg / import binding
    )
    try:
        warn_log.parent.mkdir(parents=True, exist_ok=True)
        with warn_log.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "dossier": file_path,
                        "lineno": lineno,
                        "node_line": node_line,
                        "ev_token": ev_token,
                    }
                )
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass
    try:
        print(
            f"CIRCULARITY WARN: {file_path}:{lineno} — a Verified-correct node's ev: slot "
            f"cites a prior dossier ({ev_token}) instead of a primary source. Replace with "
            f"a file:line/query, or move the dossier ref to a [[link]]/**Prior art:** field. "
            f"(Non-blocking; write proceeds.)",
            file=sys.stderr,
        )
    except Exception:  # noqa: BLE001
        pass


def check_circular_evidence(stdin_dict: dict) -> HookResult:
    """WARN-first circularity gate for MAP dossiers. NEVER blocks — always returns allow.
    On a detected circular ev: citation, emits a WARN (log + stderr) and allows the write.
    """
    allow = HookResult(allow=True, block_message="")
    tool_name = stdin_dict.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return allow
    tool_input = stdin_dict.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".md"):
        return allow

    p = Path(file_path)
    if not p.is_absolute():
        p = (_REPO_ROOT / p).resolve()

    # Trigger only on a MAP dossier: repo-relative path under docs/analyses/ AND the
    # canonical filename. Anything else → allow (out of scope for Phase 1).
    try:
        rel = p.resolve().relative_to(_REPO_ROOT.resolve())
    except (ValueError, OSError):
        return allow
    if not (
        rel.as_posix().startswith("docs/analyses/") and rel.name == _DOSSIER_BASENAME
    ):
        return allow

    content = _post_edit_content(p, tool_name, tool_input)
    if not content:
        return allow

    for lineno, node_line, ev_token in _iter_circular_nodes(content):
        _emit_warn(file_path, lineno, node_line, ev_token)
    return allow
