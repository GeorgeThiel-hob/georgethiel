"""
check_gate_evidence.py — CLI entry point for the gate-evidence primitive.

Usage:
  python3 .claude/hooks/check_gate_evidence.py --write-evidence <phase>
  python3 .claude/hooks/check_gate_evidence.py --check-phase <phase> --threshold <N>

Kit-authored CLI, reimplemented (not copied) from a pattern-source two-verb
sentinel-style CLI surface — a phase-tagged write verb and a phase-check
verb, both keyed to the current git branch. That surface's third, full-gate
verb (git-diff parsing, a hardcoded critical-path tier floor, MAP-dossier
text-parsing, transcript-backed evidence re-derivation) is deliberately NOT
reimplemented here — that logic belongs with the calling ship skill (module
`21-pipeline-skills`'s GIT variants own tier detection and the MAP-dossier
file-presence condition), not this generic evidence primitive. See module
`22-second-opinion-seat`'s README "Scope note".
"""

import subprocess
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from lib.gate_evidence import check_phase, write_evidence  # noqa: E402

_REPO_ROOT = Path(__file__).parents[2]
_EVIDENCE_BASE = _REPO_ROOT / ".claude" / "state" / "gate-evidence"


def _branch_slug() -> str:
    """Return the current branch slug, or a stable fallback outside a git repo.

    Mirrors the guarding pattern used elsewhere in this kit (e.g.
    `task_checks.require_standing_brief`): a git call that can fail (no repo,
    detached HEAD, git not on PATH) must degrade to a stable value, never
    crash the CLI.
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return "no-branch"
    branch = result.stdout.strip()
    return branch.replace("/", "-") if branch else "no-branch"


def main() -> None:
    args = sys.argv[1:]

    if len(args) >= 2 and args[0] == "--write-evidence":
        phase = args[1]
        slug = _branch_slug()
        evidence_dir = _EVIDENCE_BASE / slug
        path = write_evidence(slug, phase, evidence_dir)
        print(str(path))
        sys.exit(0)

    if len(args) >= 4 and args[0] == "--check-phase" and args[2] == "--threshold":
        phase = args[1]
        try:
            threshold = int(args[3])
        except ValueError:
            print(
                f"GATE EVIDENCE: FAIL (--threshold must be an integer, got {args[3]!r})"
            )
            sys.exit(2)
        slug = _branch_slug()
        evidence_dir = _EVIDENCE_BASE / slug
        passed = check_phase(phase, threshold, evidence_dir)
        if passed:
            print(f"GATE EVIDENCE: PASS (phase={phase}, threshold={threshold})")
            sys.exit(0)
        else:
            print(
                f"GATE EVIDENCE: FAIL (phase={phase} short of threshold={threshold}) — "
                "dispatch the second-opinion seat for this phase, then: "
                f"python3 .claude/hooks/check_gate_evidence.py --write-evidence {phase}"
            )
            sys.exit(1)

    print(
        "Usage: check_gate_evidence.py"
        " --write-evidence <phase> | --check-phase <phase> --threshold <N>",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
