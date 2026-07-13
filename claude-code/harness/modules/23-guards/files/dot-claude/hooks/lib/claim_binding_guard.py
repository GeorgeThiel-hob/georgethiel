"""claim_binding_guard.py — directive-forcing WARN gate (sub-gate A of the
claim-binding guard pair).

On a handoff-artifact Write/Edit/MultiEdit (a .md under docs/superpowers/briefs/,
docs/project-updates/, or docs/tickets/), WARNS (non-blocking) when the artifact makes
an ungrounded code-ish ABSENCE or COUNT claim about code state but binds ZERO reexec:
directives — nudging the author to attach a reexec:absent|count directive so the
reexec_guard can re-verify the claim against current-main. WARN-first (owner
decision): the guard NEVER blocks; it appends a structured line to
~/.claude/logs/claim-binding-warns.log + prints a stderr WARN, and the write proceeds.

A line WARNs only when all FOUR conditions hold: (a) it matches an absence/count
claim-shape, AND (b) it carries a co-located code-ish object, AND (c) its ±1-line window
carries NO citation token, AND (d) it is not inside a fenced code block. See the
CONVERGED MAP dossier
docs/analyses/<investigation-slug>/map-dossier.md.

stdlib-only (runs under run_python.sh = system python3, outside .venv).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from . import HookResult
from .claim_detector import CITATION_PATTERN
from .post_edit import _post_edit_content
from .reexec_guard import _fenced_line_flags, _iter_directives

# This file is .claude/hooks/lib/claim_binding_guard.py → parents[3] == project root.
_REPO_ROOT: Path = Path(__file__).parents[3]

_HOOK_NAME = "check_claim_binding"

# Warn-log path — read at CALL time (like circularity_guard._WARN_LOG), NEVER bound at
# import, so the test overlay can redirect it (else no-warn assertions pass vacuously).
_WARN_LOG: Path = Path.home() / ".claude" / "logs" / "claim-binding-warns.log"

# Handoff-artifact subdirs in scope (repo-relative, POSIX). NOT docs/analyses/
# (circularity-scoped).
_TARGET_SUBDIRS = ("docs/superpowers/briefs/", "docs/project-updates/", "docs/tickets/")

# ── (a) claim-shape: absence + count (NOT bare presence — spec §Out of scope) ──
_ABSENCE_RE = re.compile(
    r"\b(removed|deleted|dropped|eliminated|no longer (?:exists|present|used)"
    r"|absent from|gone from)\b",
    re.I,
)
_COUNT_RE = re.compile(
    r"\b(?:zero|no|\d+)\s+(?:remaining\s+)?"
    r"(?:refs?|references?|callers?|call-sites?|occurrences?|usages?|matches)\b",
    re.I,
)
_THERE_RE = re.compile(
    r"\bthere (?:is|are)\s+(?:no|zero|\d+)\b[^.\n]*"
    r"\b(?:refs?|callers?|occurrences?)\b",
    re.I,
)

# ── (b) code-ish object: a real, re-greppable token (§3.2.2 pinned) ────────────
_CODEISH_RE = re.compile(
    r"`[^`]+`"  # any backtick-delimited token
    r"|\b[\w./-]+\.(?:py|md|json|ya?ml|toml|db|sh|txt|cfg|ini)\b"  # path/file token
    r"|\b\w+\(\)"  # call form  (redeem())
    r"|\bsrc/|\btests?/|\bscripts/|\bconfig/|\.claude/"  # dir-prefixed path
)


def _is_claim_shape(line: str) -> bool:
    """(a): the line asserts an absence or a count about code state."""
    return bool(
        _ABSENCE_RE.search(line) or _COUNT_RE.search(line) or _THERE_RE.search(line)
    )


def _window(lines: list[str], i: int) -> str:
    """True ±1-line window (claim line + above + below) — matches
    claim_detector._window."""
    lo = i - 1 if i > 0 else i
    return " ".join(lines[lo : i + 2])


def _iter_target_claims(content: str) -> Iterator[int]:
    """Yield the 1-indexed line number of each line satisfying all FOUR §3.2 conditions:
    claim-shape (a) AND co-located code-ish object (b) AND no citation token in its
    ±1-line window (c) AND not inside a fenced code block (d). Pure string work — no
    FS stat, no subprocess."""
    lines = content.splitlines()
    fenced = _fenced_line_flags(lines)
    for i, line in enumerate(lines):
        if fenced[i]:  # (d)
            continue
        if not _is_claim_shape(line):  # (a)
            continue
        if not _CODEISH_RE.search(line):  # (b)
            continue
        if CITATION_PATTERN.search(_window(lines, i)):  # (c)
            continue
        yield i + 1


def _has_reexec_directive(content: str) -> bool:
    """True iff the artifact binds >=1 well-formed reexec: directive outside fenced code
    (document-level model, §3.3). Reuses the reexec_guard's fence-aware directive
    detection."""
    return any(True for _ in _iter_directives(content))


def _emit_warn(file_path: str, claim_linenos: list[int]) -> None:
    """Append a structured JSON warn record to _WARN_LOG (dereferenced at CALL time so a
    test overlay can redirect it) + print a stderr WARN. Best-effort — never raises."""
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
                        "artifact": file_path,
                        "claim_linenos": claim_linenos,
                    }
                )
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass
    try:
        lines_str = ", ".join(str(n) for n in claim_linenos)
        print(
            f"CLAIM-BINDING WARN: {file_path} makes an ungrounded code-ish "
            f"absence/count claim (line(s) {lines_str}) but binds no reexec: "
            f"directive. Consider adding a reexec:absent|count directive so a "
            f"later gate can re-verify it against current-main. "
            f"(Non-blocking; write proceeds.)",
            file=sys.stderr,
        )
    except Exception:  # noqa: BLE001
        pass


def check_claim_binding(stdin_dict: dict) -> HookResult:
    """WARN-first directive-forcing gate for handoff artifacts. NEVER blocks — always
    allow. On an in-scope artifact with >=1 unbound code-ish absence/count claim and
    zero reexec: directives, emits ONE warn (log + stderr) and allows the write."""
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

    # Trigger only on an in-scope handoff artifact. Anything else (incl.
    # docs/analyses/) → allow.
    try:
        rel = p.resolve().relative_to(_REPO_ROOT.resolve())
    except (ValueError, OSError):
        return allow
    rel_posix = rel.as_posix()
    if not any(rel_posix.startswith(sub) for sub in _TARGET_SUBDIRS):
        return allow

    content = _post_edit_content(p, tool_name, tool_input)
    if not content:
        return allow

    if _has_reexec_directive(content):  # §3.4 step 5: already bound → nothing to nudge
        return allow

    claims = list(_iter_target_claims(content))
    if claims:
        _emit_warn(file_path, claims)
    return allow
