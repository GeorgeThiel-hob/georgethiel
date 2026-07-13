"""
gate_evidence.py — the gate-evidence primitive: record a call, count calls per
phase, compare a phase's count to a caller-supplied threshold.

Generalizes a common hard rule ("write a marker before every gated
second-opinion call, then count markers against the COUNT of required
phase-gates before shipping") into a project-agnostic mechanism with no
dependency on any specific advisor tool, model, or pipeline shape.
Reimplemented here from scratch (not copied) as `write_evidence` /
`count_evidence` / `check_phase`, with one shape change: this `check_phase`
takes a CALLER-supplied required count instead of returning bare phase
presence, because this kit's routing profiles set a per-tier COUNT of
required phase-gates (see `docs/harness/22-second-opinion-seat.md`) — each
phase-gate is itself always checked at `--threshold 1` — rather than a single
hardcoded constant.

Provides:
  write_evidence(branch_slug: str, phase: str, evidence_dir: Path) -> Path
  count_evidence(phase: str, evidence_dir: Path) -> int
  check_phase(phase: str, required_count: int, evidence_dir: Path) -> bool

No phase allowlist is enforced here — the calling skill (module
`21-pipeline-skills`) owns which phase names are meaningful for its own
pipeline. This module only writes, counts, and compares; it has zero
project-specific values baked in (see the module README's Scope note).
"""

import os
import tempfile
from pathlib import Path

# REVIEW's dual-writer convention (module `21-pipeline-skills`' REVIEW variant,
# Step 4b + Step 6): a re-verify call recorded under "audit-fix" (after a
# P0/P1 fix batch) substitutes for the clean-pass "audit" gate evidence it
# precedes — either alone satisfies the ship check's
# `--check-phase audit --threshold N`. This is the ONE named exception to an
# otherwise phase-blind counter; every other phase string is treated
# identically with no special-casing.
_AUDIT_PHASE = "audit"
_AUDIT_FIX_PHASE = "audit-fix"


def write_evidence(branch_slug: str, phase: str, evidence_dir: Path) -> Path:
    """Write one phase-tagged evidence marker file. Atomic via temp+os.replace.

    `branch_slug` is accepted for interface parity with the pattern this is
    sourced from (a caller may want it for logging) but is not itself part of
    the marker filename — `evidence_dir` is already per-branch
    (`.claude/state/gate-evidence/<branch-slug>/`), so re-encoding the slug
    into the filename would be redundant.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    existing = list(evidence_dir.glob("evidence-*.touch"))
    seq = len(existing) + 1
    target = evidence_dir / f"evidence-{seq:03d}-{phase}.touch"
    fd, tmp_path = tempfile.mkstemp(dir=str(evidence_dir), prefix=".tmp-")
    try:
        os.close(fd)
        os.replace(tmp_path, str(target))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return target


def count_evidence(phase: str, evidence_dir: Path) -> int:
    """Count evidence marker files tagged with the given phase.

    Returns 0 if evidence_dir does not exist. Matches files ending in
    '-{phase}.touch' — e.g. 'evidence-002-spec.touch' matches phase='spec'.
    """
    if not evidence_dir.exists():
        return 0
    return len(list(evidence_dir.glob(f"*-{phase}.touch")))


def check_phase(phase: str, required_count: int, evidence_dir: Path) -> bool:
    """True iff recorded evidence for `phase` meets required_count.

    `required_count` is a CALLER-supplied argument, never a module-level
    constant in this file — it is the COUNT of required phase-gates, a
    routing-profile parameter (PRO / MAX5 / MAX20 each set their own per-tier
    counts; a `-RISK` tier suffix adds one more required phase-gate at the
    CALL SITE, not here — see the module README's deletion-test note and
    `docs/harness/22-second-opinion-seat.md`). Every individual phase-gate
    check itself is always invoked at `--threshold 1`.

    One named exception: when phase == "audit", evidence recorded under
    "audit-fix" also counts toward the total (the dual-writer convention
    documented above) — a re-verify call after a P0/P1 fix batch substitutes
    for the clean-pass audit call it precedes.
    """
    count = count_evidence(phase, evidence_dir)
    if phase == _AUDIT_PHASE:
        count += count_evidence(_AUDIT_FIX_PHASE, evidence_dir)
    return count >= required_count
