"""
task_checks.py — Hook 7 (plan-by-reference) and Hook 8 (standing brief).

Each check is a pure function: (stdin_dict: dict) -> HookResult.
No side effects.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional

from . import HookResult, log_hook_error
from .brief_paths import resolve_brief_path
from .tier_detection import RISK_PREFIXES, detect_tier_promotion

# .claude/hooks/lib/../../.. = project root
_REPO_ROOT: Path = Path(__file__).parents[3]

# ── Constants ────────────────────────────────────────────────────────────────

_PLAN_CONTENT_PATTERNS = [
    re.compile(r"^### Task \d+", re.MULTILINE),
    re.compile(r"^## Task \d+", re.MULTILINE),
    re.compile(r"Acceptance criteria:", re.IGNORECASE),
    re.compile(r"^- \[ \]", re.MULTILINE),
]
_PLAN_CONTENT_CHECKLIST_MIN = 5  # need ≥5 checklist items to be a candidate
_LINE_RANGE_PATTERN = re.compile(r"lines\s+(\d+)-(\d+)\s+of\s+(\S+\.md)", re.IGNORECASE)
_WHITELIST_ESCAPE = "# no-plan-ref-check"

# Threshold below which we never block (too small to be an inlined task body)
_MIN_PROMPT_LENGTH = 1500

# Hook 8 keywords that indicate the dispatch IS the brief-writing or plan-writing.
# '# t1-no-brief' is the T1 escape: micro-tickets skip the brief phase by design.
_BRIEF_WRITING_KEYWORDS = ("standing brief", "write the brief", "# t1-no-brief")
# Pre-brief dispatches: plan-writing AND T3 research/debate/brainstorming phases
_PRE_BRIEF_KEYWORDS = (
    "writing-plans",
    "write the plan",
    "draft the plan",
    "council",
    "/council",
    "brainstorm",
    "brainstorming",
    "debate",
    "/debate",
    "[map-verifier]",  # A4: MAP adversarial-verifier dispatch bypasses the brief gate
    "[checkpoint]",  # E10: /CHECKPOINT dispatch bypass (cf [map-verifier])
)


# ── Hook 7 ───────────────────────────────────────────────────────────────────


def _resolve_line_range_refs(prompt: str) -> Optional[HookResult]:
    """Resolve every ``lines X-Y of <file>.md`` reference in a candidate prompt.

    Returns a blocking HookResult for the FIRST reference whose file does not
    exist or whose range is out of bounds; None if every reference resolves.

    Fails OPEN (returns None) on any I/O or unexpected error: this is an
    execute-phase dispatch gate, so a false block would wedge a live subagent
    dispatch (mirrors _check_tier_divergence degrading to [] on git error).
    """
    try:
        for m in _LINE_RANGE_PATTERN.finditer(prompt):
            start = int(m.group(1))
            end = int(m.group(2))
            # Strip wrapping delimiters — Rule 7 dispatches wrap the path in
            # backticks; greedy \S+\.md keeps a leading backtick otherwise.
            rel_path = m.group(3).strip("`'\"")
            target = _REPO_ROOT / rel_path
            if not target.is_file():
                return HookResult(
                    allow=False,
                    block_message=(
                        f"plan-by-reference rule violation: cited file "
                        f"'{rel_path}' does not exist. Fix the reference or add "
                        "'# no-plan-ref-check' to bypass."
                    ),
                )
            line_count = len(target.read_text(encoding="utf-8").splitlines())
            if start < 1 or start > end or end > line_count:
                return HookResult(
                    allow=False,
                    block_message=(
                        f"plan-by-reference rule violation: cited range "
                        f"{start}-{end} is out of bounds for '{rel_path}' "
                        f"(file has {line_count} lines). Fix the reference or "
                        "add '# no-plan-ref-check' to bypass."
                    ),
                )
        return None
    except Exception as exc:  # noqa: BLE001 — fail-OPEN: never wedge a dispatch
        log_hook_error("check_plan_by_reference", str(exc))
        return None


def check_plan_by_reference(stdin_dict: dict) -> HookResult:
    """
    Hook 7 — block inlined plan task bodies in Task dispatches.

    Allow if:
    - prompt length < 1500 chars
    - prompt does not contain plan-content markers
    - prompt contains a line-range reference (lines X-Y of <plan>.md)
    - whitelist escape '# no-plan-ref-check' is present
    Block if: long prompt with plan-content markers and no line-range reference.
    """
    prompt: str = stdin_dict.get("tool_input", {}).get("prompt", "")

    if _WHITELIST_ESCAPE in prompt:
        return HookResult(allow=True, block_message="")

    if len(prompt) < _MIN_PROMPT_LENGTH:
        return HookResult(allow=True, block_message="")

    # Check for plan-content markers
    is_candidate = False
    checklist_items = len(re.findall(r"^- \[ \]", prompt, re.MULTILINE))
    has_checklist = checklist_items >= _PLAN_CONTENT_CHECKLIST_MIN
    has_task_header = bool(
        _PLAN_CONTENT_PATTERNS[0].search(prompt)
        or _PLAN_CONTENT_PATTERNS[1].search(prompt)
    )
    has_acceptance = bool(_PLAN_CONTENT_PATTERNS[2].search(prompt))

    if (has_task_header or has_acceptance) or has_checklist:
        is_candidate = True

    if not is_candidate:
        return HookResult(allow=True, block_message="")

    # Candidate: must have a line-range reference that RESOLVES (path exists +
    # range in-bounds) to pass. Fail-OPEN on I/O error (never wedge a dispatch).
    if _LINE_RANGE_PATTERN.search(prompt):
        block = _resolve_line_range_refs(prompt)
        return block if block is not None else HookResult(allow=True, block_message="")

    return HookResult(
        allow=False,
        block_message=(
            "plan-by-reference rule violation: inline task body detected. "
            "Re-dispatch with 'Read lines X-Y of docs/superpowers/plans/<plan>.md "
            "and implement that task.' "
            "Add '# no-plan-ref-check' to bypass for legitimate large prompts."
        ),
    )


# ── Hook 8 ───────────────────────────────────────────────────────────────────


def require_standing_brief(stdin_dict: dict) -> HookResult:
    """
    Hook 8 — require standing brief on ticket branches.

    Allow if:
    - branch is main or master
    - brief file exists at docs/superpowers/briefs/<branch-slug>.md
    - prompt contains standing-brief writing keywords (first dispatch writes the brief)
    - prompt contains plan-writing keywords (pre-brief plan-writing phase)
    Block otherwise.
    """
    prompt: str = stdin_dict.get("tool_input", {}).get("prompt", "")

    # Get current branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            check=True,
            cwd=str(_REPO_ROOT),
        )
        branch = result.stdout.decode().strip()
    except subprocess.CalledProcessError:
        # can't determine branch → allow
        return HookResult(allow=True, block_message="")

    if branch in ("main", "master", ""):
        return HookResult(allow=True, block_message="")

    # Build brief path
    branch_slug = branch.replace("/", "-")
    brief_path = resolve_brief_path(branch_slug, _REPO_ROOT)

    if brief_path.exists():
        divergence = _check_tier_divergence(brief_path)
        if divergence is not None:
            return divergence
        return HookResult(allow=True, block_message="")

    # Brief doesn't exist — check if this IS the brief-writing dispatch
    prompt_lower = prompt.lower()
    if any(kw in prompt_lower for kw in _BRIEF_WRITING_KEYWORDS):
        return HookResult(allow=True, block_message="")
    if any(kw in prompt_lower for kw in _PRE_BRIEF_KEYWORDS):
        return HookResult(allow=True, block_message="")

    return HookResult(
        allow=False,
        block_message=(
            f"standing-brief rule violation: no brief at `{brief_path}`. "
            f"First dispatch of each ticket's execute phase must be "
            f"'write the standing brief to {brief_path}' "
            f"before any implementation task."
        ),
    )


# ── Tier divergence helper ───────────────────────────────────────────────────


def _check_tier_divergence(brief_path: Path) -> Optional[HookResult]:
    """Read declared tier from brief, compare against git diff. Return a blocking
    HookResult if the diff contains RISK paths that upgrade the declared tier,
    else None (no divergence, allow).
    """
    # Parse **Tier:** from brief
    try:
        brief_text = brief_path.read_text(encoding="utf-8")
    except OSError:
        return None

    tier_match = re.search(r"\*\*Tier:\*\*\s*(\S+)", brief_text)
    if not tier_match:
        return None
    declared_tier = tier_match.group(1).strip()

    # Get diff paths against main
    try:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(_REPO_ROOT),
        )
        diff_paths = [p for p in diff_result.stdout.strip().split("\n") if p]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        diff_paths = []

    promoted = detect_tier_promotion(diff_paths, declared_tier)
    if promoted is None or promoted == declared_tier:
        return None

    matching = next(
        (
            p
            for p in diff_paths
            if any(p == pre or p.startswith(pre) for pre in RISK_PREFIXES)
        ),
        "<unknown>",
    )
    return HookResult(
        allow=False,
        block_message=(
            f"tier-divergence: path '{matching}' auto-promotes this ticket to {promoted}; "
            f"update standing brief **Tier:** from {declared_tier} to {promoted} "
            f"and re-verify the tier scope before continuing."
        ),
    )
