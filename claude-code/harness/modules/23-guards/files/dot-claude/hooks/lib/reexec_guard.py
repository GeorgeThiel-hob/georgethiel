"""reexec_guard.py — recompute-and-compare PreToolUse guard.

Re-runs structured `reexec` directives embedded in markdown handoff artifacts at
Write/Edit/MultiEdit time and BLOCKS on a clean contradiction. The core
recompute *primitive* of the born-clean layer: a declared directive means
something — the hook actually re-greps the current tree and compares (the
one principle: recompute-and-compare, never confirm-a-string-is-present).

Directive syntax (HTML comment; recognized ONLY outside fenced code blocks):
    <!-- reexec:absent  pattern="TOKEN" path="DIR_OR_FILE" -->   (expect 0 matches)
    <!-- reexec:present pattern="TOKEN" path="DIR_OR_FILE" -->   (expect >=1 match)
    <!-- reexec:count   pattern="TOKEN" path="DIR_OR_FILE" n="N" --> (expect ==N lines)

Fail-open discipline (Guard 5): an UNVERIFIABLE directive (malformed, path-escape,
grep exec-error/timeout, grep-not-found) → allow + log. Only a CLEANLY-EXECUTED
grep whose result contradicts the assertion → block. A well-formed in-repo path
that does not exist → block (stale directive path). unverifiable != false.

stdlib-only (runs under run_python.sh = system python3, outside .venv).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Iterator, Optional

from . import HookResult, log_hook_error
from .post_edit import _post_edit_content

# This file is .claude/hooks/lib/reexec_guard.py → parents[3] == project root.
# Mirrors this convention used by sibling lib modules in this package.
_REPO_ROOT: Path = Path(__file__).parents[3]

_HOOK_NAME = "check_reexec_directives"

# Per-file safety cap (N-cap): a file with >50 directives fails open + logs.
_MAX_DIRECTIVES = 50

# Line-scoped directive match (no DOTALL). claim in {absent, present, count};
# attrs excludes '>' so the closing '-->' is never consumed.
_DIRECTIVE_RE = re.compile(
    r"<!--\s*reexec:(?P<claim>absent|present|count)\s+(?P<attrs>[^\n>]*?)\s*-->"
)
# key="value" — value stops at the first '"' (no escaping, per spec §3.2).
_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')

# Fence open/marker: 0-3 leading spaces, then a run of >=3 backticks or tildes
# (CommonMark §4.5). Info-strings (```python) are allowed on the OPENING fence.
_FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})")


def _fenced_line_flags(lines: list[str]) -> list[bool]:
    """Per-line bool: True iff the line is INSIDE (or is the boundary of) a fenced
    code block. A fence opens on a >=3 run of ` or ~ with 0-3 indent; it closes
    ONLY on a later line whose fence uses the SAME char, length >= the opener, and
    consists of nothing but the fence run (CommonMark). An unterminated fence
    extends to EOF (those lines count fenced → skipped — the safe direction)."""
    inside = [False] * len(lines)
    open_char = ""
    open_len = 0
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if open_len == 0:
            if m:
                run = m.group("fence")
                open_char, open_len = run[0], len(run)
                inside[i] = True  # the opening fence line itself
        else:
            inside[i] = True  # within the block
            if m:
                run = m.group("fence")
                if (
                    run[0] == open_char
                    and len(run) >= open_len
                    and line.strip() == run  # closer is bare (no info string)
                ):
                    open_char, open_len = "", 0
    return inside


def _iter_directives(content: str) -> Iterator[tuple[str, dict, int]]:
    """Yield (claim, attrs, lineno) for each reexec directive NOT inside a fenced
    code block. lineno is 1-indexed (for messages)."""
    lines = content.splitlines()
    fenced = _fenced_line_flags(lines)
    for i, line in enumerate(lines):
        if fenced[i]:
            continue
        for m in _DIRECTIVE_RE.finditer(line):
            attrs = dict(_ATTR_RE.findall(m.group("attrs")))
            yield m.group("claim"), attrs, i + 1


def _grep_line_count(pattern: str, target: Path) -> Optional[int]:
    """Run `grep -rIFn -e <pattern> -- <target>` and return the matching-LINE
    count, or None on an execution error (fail-open). rc0=matches, rc1=valid
    zero, rc2/timeout/OSError=error."""
    argv = ["grep", "-rIFn", "-e", pattern, "--", str(target)]
    try:
        proc = subprocess.run(argv, cwd=str(_REPO_ROOT), capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode == 0:
        # Exact grep line count; splitlines() over-counts on \f,\v,\x85,U+2028.
        return proc.stdout.count(b"\n")
    if proc.returncode == 1:
        return 0  # zero matches is a VALID result, not an error
    return None  # rc==2 on an existing path → genuine grep error → fail-open


def _check_one(
    claim: str, attrs: dict, lineno: int, file_path: str
) -> Optional[HookResult]:
    """Return a BLOCKING HookResult, or None to allow (verified-ok or fail-open)."""
    pattern = attrs.get("pattern", "")
    rel_path = attrs.get("path", "")

    # Field validation → unverifiable → fail-open.
    if not pattern or not pattern.strip() or "\n" in pattern:
        log_hook_error(
            _HOOK_NAME, f"{file_path}:{lineno} empty/invalid pattern; fail-open"
        )
        return None
    if not rel_path:
        log_hook_error(_HOOK_NAME, f"{file_path}:{lineno} missing path; fail-open")
        return None
    expected_n = None
    if claim == "count":
        n_raw = attrs.get("n", "")
        if not n_raw.isdigit():
            log_hook_error(
                _HOOK_NAME, f"{file_path}:{lineno} count needs integer n; fail-open"
            )
            return None
        expected_n = int(n_raw)

    # Path confinement → escape → fail-open.
    root = _REPO_ROOT.resolve()
    target = (root / rel_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        log_hook_error(
            _HOOK_NAME, f"{file_path}:{lineno} path escapes repo: {rel_path}; fail-open"
        )
        return None

    # Existence pre-check: nonexistent in-repo path → BLOCK (stale directive path).
    if not target.exists():
        return HookResult(
            allow=False,
            block_message=(
                f"reexec guard: directive at {file_path}:{lineno} points at "
                f"'{rel_path}', which does not exist under the repo root — this is a "
                f"stale directive path (moved/renamed file). Fix the path or remove "
                f"the claim, then re-run."
            ),
        )

    # Recompute.
    count = _grep_line_count(pattern, target)
    if count is None:
        log_hook_error(_HOOK_NAME, f"{file_path}:{lineno} grep exec error; fail-open")
        return None

    # Compare.
    violated = (
        (claim == "absent" and count >= 1)
        or (claim == "present" and count == 0)
        or (claim == "count" and count != expected_n)
    )
    if not violated:
        return None
    expected_str = {"absent": "0", "present": ">=1"}.get(claim, str(expected_n))
    return HookResult(
        allow=False,
        block_message=(
            f"reexec guard: directive at {file_path}:{lineno} asserts "
            f'reexec:{claim} pattern="{pattern}" path="{rel_path}" '
            f"(expected {expected_str} matching lines) but a fresh "
            f"`grep -rIFn -e {pattern!r} -- {rel_path}` found {count}. "
            f"Re-run the grep and correct or remove the claim before writing."
        ),
    )


def check_reexec_directives(stdin_dict: dict) -> HookResult:
    """Recompute-and-compare guard for `reexec` directives in markdown handoff files.

    Triggers only on Edit/Write/MultiEdit of a `.md` file whose post-edit content
    carries a reexec directive OUTSIDE a fenced code block. Fail-open on any
    unverifiable directive; BLOCK on a clean contradiction or a stale (nonexistent)
    directive path.
    """
    tool_name = stdin_dict.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return HookResult(allow=True, block_message="")
    tool_input = stdin_dict.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not file_path.endswith(".md"):
        return HookResult(allow=True, block_message="")

    p = Path(file_path)
    if not p.is_absolute():
        p = (_REPO_ROOT / p).resolve()

    content = _post_edit_content(p, tool_name, tool_input)
    if not content:
        return HookResult(allow=True, block_message="")

    directives = list(_iter_directives(content))
    if not directives:
        return HookResult(allow=True, block_message="")
    if len(directives) > _MAX_DIRECTIVES:
        log_hook_error(
            _HOOK_NAME,
            f"{file_path}: {len(directives)} directives exceeds cap "
            f"{_MAX_DIRECTIVES}; fail-open (no partial verification)",
        )
        return HookResult(allow=True, block_message="")

    for claim, attrs, lineno in directives:
        result = _check_one(claim, attrs, lineno, file_path)
        if result is not None and not result.allow:
            return result
    return HookResult(allow=True, block_message="")
