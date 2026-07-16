"""
pretooluse_dispatcher.py — PreToolUse hook entry point.

Reads JSON from stdin, routes to check functions by tool_name,
writes JSON to stdout ONLY on block: {"decision": "block", "message": "..."} — an
allowed call emits nothing (empty stdout + exit 0 is the allow signal).

Safety: all checks are wrapped in try/except — a broken check fails open (allow)
and logs the exception to ~/.claude/logs/hook-errors.log.

Kit note: every optional check below is import-guarded (see `_maybe_register`) —
this dispatcher is the shared substrate every hook-carrying module plugs into, and
an adopter may install any subset of those modules. A missing optional lib file (a
module the adopter did not select), or a shipped lib file that only exports a
subset of a check's source functions, must never crash this dispatcher — it must
simply mean that check does not register, and dispatch() treats it as inert.
"""

import importlib
import json
import re as _re
import subprocess as _sp
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Ensure .claude/hooks/ is on sys.path regardless of cwd
_HOOKS_DIR = Path(__file__).parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

_ERROR_LOG = Path.home() / ".claude" / "logs" / "hook-errors.log"
_REPO_ROOT = Path(__file__).parent.parent.parent

# Registry of optional checks actually available in this install. Populated by
# _maybe_register() below — never assume a key is present; always look it up
# with _CHECKS.get(name), which returns None for anything not shipped.
_CHECKS: dict[str, Any] = {}


def _maybe_register(import_path: str, check_fn_name: str) -> None:
    """Register check_fn_name from lib.<import_path> into _CHECKS, if present.

    This kit ships lib/ check modules à la carte, one per hook-carrying module
    the adopter may or may not have selected. Two distinct absences must both
    degrade to "this check simply doesn't register," never to a crash:
      1. the whole lib file is missing (module not installed) — import_module
         raises ImportError;
      2. the lib file IS installed but only ships a subset of the source
         file's functions (e.g. this kit's task_checks.py variant drops
         check_ac_id_prefix / block_finishing_branch_skill) — getattr raises
         AttributeError.
    Both are caught here so a partial or absent optional module never prevents
    the dispatcher itself from loading.
    """
    try:
        module = importlib.import_module(f"lib.{import_path}")
        _CHECKS[check_fn_name] = getattr(module, check_fn_name)
    except (ImportError, AttributeError):
        pass  # optional — not shipped in this install, fail open


_maybe_register("brief_paths", "resolve_brief_path")
_maybe_register("circularity_guard", "check_circular_evidence")
_maybe_register("claim_binding_guard", "check_claim_binding")
_maybe_register("reexec_guard", "check_reexec_directives")
_maybe_register("task_checks", "block_finishing_branch_skill")
_maybe_register("task_checks", "check_ac_id_prefix")
_maybe_register("task_checks", "check_plan_by_reference")
_maybe_register("task_checks", "require_standing_brief")
_maybe_register("seat_checks", "check_seat_routing")


def _find_branch_spec() -> Optional[Path]:
    """Return the spec path for the current branch, or None if not determinable.

    Lookup order:
    1. Read docs/superpowers/briefs/<branch-slug>.md, parse **Spec:** line.
    2. Fallback: most-recently-modified docs/superpowers/specs/*.md.
    3. Return None if main/master branch, no brief, and no specs found.
    """
    try:
        result = _sp.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            check=True,
            cwd=str(_REPO_ROOT),
        )
        branch = result.stdout.decode().strip()
    except Exception:
        return None

    if branch in ("main", "master", ""):
        return None

    branch_slug = branch.replace("/", "-")
    resolve_brief_path = _CHECKS.get("resolve_brief_path")
    if resolve_brief_path is not None:
        brief_path = resolve_brief_path(branch_slug, _REPO_ROOT)

        if brief_path.exists():
            try:
                text = brief_path.read_text(encoding="utf-8")
                m = _re.search(r"\*\*Spec:\*\*\s*(\S+)", text)
                if m:
                    spec_path = _REPO_ROOT / m.group(1)
                    if spec_path.exists():
                        return spec_path
            except OSError:
                pass

    # Fallback: most-recently-modified spec file
    specs_dir = _REPO_ROOT / "docs" / "superpowers" / "specs"
    if specs_dir.is_dir():
        specs = sorted(
            specs_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if specs:
            return specs[0]

    return None


def _safe_check(fn, stdin_dict: Any) -> dict:
    """
    Run check fn(stdin_dict) inside a try/except.
    Returns {"decision": "allow"} on exception (fail open) and logs the error.
    """
    try:
        result = fn(stdin_dict)
        if result.allow:
            return {"decision": "allow"}
        return {"decision": "block", "message": result.block_message}
    except Exception as exc:  # noqa: BLE001
        try:
            _ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _ERROR_LOG.open("a") as fh:
                fh.write(
                    json.dumps(
                        {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "hook": fn.__name__,
                            "error": str(exc),
                        }
                    )
                    + "\n"
                )
        except Exception:  # noqa: BLE001
            pass  # log-write failed — still fail open, do not raise
        return {"decision": "allow"}


def dispatch(stdin_dict: dict) -> dict:
    """Route stdin_dict to the appropriate check(s) and return a decision dict."""
    tool_name = stdin_dict.get("tool_name", "")

    if tool_name in ("Task", "Agent"):
        # Hook 7 first — if it blocks, short-circuit
        check_plan_by_reference = _CHECKS.get("check_plan_by_reference")
        if check_plan_by_reference is not None:
            result = _safe_check(check_plan_by_reference, stdin_dict)
            if result["decision"] == "block":
                return result
        # Hook 8 — capture-and-continue (was an unconditional return) so the
        # seat check can still run when the brief gate passes.
        require_standing_brief = _CHECKS.get("require_standing_brief")
        if require_standing_brief is not None:
            result = _safe_check(require_standing_brief, stdin_dict)
            if result["decision"] == "block":
                return result
        # Seat routing check (KIT-SEAT-ENFORCE-01) — last in the branch.
        check_seat_routing = _CHECKS.get("check_seat_routing")
        if check_seat_routing is not None:
            return _safe_check(check_seat_routing, stdin_dict)
        return {"decision": "allow"}

    if tool_name in ("Edit", "Write", "MultiEdit"):
        # E3: reexec recompute-and-compare guard — block a stale/contradicted directive
        check_reexec_directives = _CHECKS.get("check_reexec_directives")
        if check_reexec_directives is not None:
            result = _safe_check(check_reexec_directives, stdin_dict)
            if result["decision"] == "block":
                return result
        # E4: circularity WARN gate — never blocks (side-effect warn only),
        # does not short-circuit
        check_circular_evidence = _CHECKS.get("check_circular_evidence")
        if check_circular_evidence is not None:
            _safe_check(check_circular_evidence, stdin_dict)
        # Sub-gate A: claim-binding WARN gate — never blocks (side-effect warn only),
        # does not short-circuit
        check_claim_binding = _CHECKS.get("check_claim_binding")
        if check_claim_binding is not None:
            _safe_check(check_claim_binding, stdin_dict)
        return {"decision": "allow"}

    if tool_name == "Skill":
        # Hook 12: block finishing-a-development-branch first
        result = {"decision": "allow"}
        block_finishing_branch_skill = _CHECKS.get("block_finishing_branch_skill")
        if block_finishing_branch_skill is not None:
            result = _safe_check(block_finishing_branch_skill, stdin_dict)
            if result["decision"] == "block":
                return result
        # Hook 19: AC-N prefix enforcement on writing-plans invocation
        check_ac_id_prefix = _CHECKS.get("check_ac_id_prefix")
        if (
            check_ac_id_prefix is not None
            and stdin_dict.get("tool_input", {}).get("skill")
            == "superpowers:writing-plans"
        ):
            spec_path = _find_branch_spec()
            if spec_path is not None:
                return _safe_check(check_ac_id_prefix, spec_path)
        return result

    # Unknown tool → allow
    return {"decision": "allow"}


def main() -> None:
    """Entry point for PreToolUse hook.

    Fails open at every layer: stdin parse, dispatch, and stdout write.
    Always exits 0 so the hook never wedges the session.
    """
    stdin_dict: dict = {}
    try:
        stdin_dict = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        pass  # fall through with empty dict — dispatch handles unknown tool

    try:
        response = dispatch(stdin_dict)
    except Exception:  # noqa: BLE001
        response = {"decision": "allow"}

    # FIX-HOOK-ALLOW-NOISE-01 (kit port): emit stdout ONLY on block. Allow →
    # empty stdout + exit 0 (Claude Code: "no output means the hook has no
    # decision to report"). Emission failure → emit nothing (fail open),
    # matching the module contract "fails open at every layer".
    if response.get("decision") == "block":
        try:
            print(json.dumps(response))
        except Exception:  # noqa: BLE001
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
