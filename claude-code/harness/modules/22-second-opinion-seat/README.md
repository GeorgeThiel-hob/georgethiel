# Module 22 — second-opinion-seat

**Purpose:** two things bundled together because they're two halves of the same
convention. (1) The **second-opinion-seat abstraction** — a fresh-context review
call at a gate (spec, plan, ship, a post-fix re-verify) is "the advisor tool if
this environment has one, else a fresh-context subagent on the strongest
affordable model," never a bare model-name reference. (2) The **gate-evidence
primitive** — a caller-supplied phase gets a marker file written before the
seat call, and a ship-time check counts those markers against a
caller-supplied threshold. Module `21-pipeline-skills`' four skills are the
only present callers of both halves; this module ships neither a pipeline nor
a tier system of its own.

**Dependencies:** none required. Module `20-tier-system`'s `-RISK` suffix is
read only by the CALLING skill (module 21's GIT variants), never by this
module's own code — see "The `-RISK` threshold bump" below. Every profile
that installs module 21 also installs this module (module 21 declares it a
required dependency), but this module's own files have no import-time or
runtime dependency on 20 or 21.

**ADAPT notes:** none. Thresholds come from the resolved routing profile
(`profiles/routing-{PRO,MAX5,MAX20}.md`), not a project-specific value —
there is nothing here for an adopter to fill in.

## What ships here

- `files/dot-claude/hooks/lib/gate_evidence.py` — kit-authored, pattern-sourced
  from a similar write-a-marker/count-markers/compare-to-threshold convention
  (a caller-supplied phase gets a marker written, then a count is compared
  against a required threshold; the file body was NOT copied — this is a
  fresh implementation). Three functions:
  `write_evidence(branch_slug, phase, evidence_dir) -> Path`,
  `count_evidence(phase, evidence_dir) -> int`,
  `check_phase(phase, required_count, evidence_dir) -> bool`.
- `files/dot-claude/hooks/check_gate_evidence.py` — kit-authored CLI,
  reimplemented (not copied) from a similar phase-tagged write-verb /
  phase-check-verb two-verb surface. Two verbs here:
  `--write-evidence <phase>` and `--check-phase <phase> --threshold <N>`.
- `files/docs/harness/22-second-opinion-seat.md` — seat-dispatch instructions
  per routing profile, the `-RISK` threshold-bump rule, and the
  enforcement-strength honesty statement in full.
- `claude-md-block.md` — the short CLAUDE.md digest every profile installs.

## Scope note — not a verbatim port

The origin pattern this module generalizes lives in a project-specific
sentinel-tracking library plus its CLI entry point. That source additionally
defines a full-gate check function (git-diff parsing, a hardcoded
critical-path tier floor, MAP-dossier `Status: CONVERGED` text-parsing) and a
CLI `--check` verb wrapping diff-reading, size-proxy, and playbook-slots
helpers. **NONE of that ports into this module.** The MAP-dossier check is
redistributed into module 21's GIT skill variants as their own simpler
dossier-file-presence condition (a plain Read/Glob check, not a
transcript-backed evidence store), and the playbook-slots check is module
`30-reasoning-playbooks`'s own file. This module ships ONLY the generic
"record a call, count calls, compare to a threshold" primitive — see
`docs/harness/22-second-opinion-seat.md` for the full accounting of what
stayed at the call site instead.

## The `-RISK` phase-set bump — documented here, not coded here

The routing profile's per-tier number (e.g. MAX5's `{T2: 2}`) is a COUNT of
required phase-gates, never the `--threshold` value passed to any single
`--check-phase` call — every phase is always checked at `--threshold 1`. The
CALLING skill (module 21's GIT variants) derives the required phase SET this
count names (spec/audit/plan) and, for a `-RISK` tier, adds the next phase in
`[spec, audit, plan]` not already required, capped at all 3 phases —
higher-consequence (`-RISK`) tickets raise the required-phase count by one,
mirroring a base+1 escalation pattern, expressed as a phase-set expansion
rather than a threshold increment. This module's own code never reads a tier string and never
applies the bump.

**Deletion-test note** (`docs/harness/26-code-discipline.md`): if this logic
lived inside `gate_evidence.py` instead, deleting module `20-tier-system`
(the `-RISK` semantics) would leave dead tier-suffix logic entangled in the
generic evidence module. Keeping it at the call site is the deeper split —
module 20 owns tier semantics, module 22 owns evidence counting, and neither
module needs to know the other's internals. Full worked table:
`docs/harness/22-second-opinion-seat.md`.

## The `audit`/`audit-fix` substitution

`check_phase`'s one named exception: when checking `phase == "audit"`,
evidence recorded under `"audit-fix"` also counts toward the total. This is
module 21's REVIEW variant's dual-writer convention — a re-verify call after a
P0/P1 fix batch (written as `audit-fix`) substitutes for the clean-pass audit
call it precedes (written as `audit`), and the ship check accepts either.
Everything else in this module treats every phase string identically; this
is the only phase-aware branch in the whole file.

## Directory layout

```
.claude/state/gate-evidence/<branch-slug>/
  evidence-001-spec.touch
  evidence-002-audit.touch
  overrides.log
```

This module's code only ever writes `evidence-NNN-<phase>.touch` files under
a per-branch directory. `overrides.log` lives in the same directory but is
written directly by module 21's GIT skill variants (the logged-override escape
hatch), never by this module's own code — see that module's README for the
JSON line shape.

## Kit-variant deltas (AC-6)

**AC-6 delta name:** "advisor→seat rewrite" — every reference to a bare
advisor tool is replaced with the second-opinion-seat abstraction (the
advisor tool if this environment has one, else a fresh-context subagent);
see `docs/harness/22-second-opinion-seat.md` for the full seat-dispatch
instructions this delta produces.

## Interfaces

Module `21-pipeline-skills`' four skills are this module's only callers:

- REVIEW (both variants) calls `--write-evidence audit-fix` at its post-fix
  re-verify gate and `--write-evidence audit` on a clean Step-6 report.
- MAP calls `--write-evidence audit` at its post-loop second-opinion synthesis
  step (idempotent with REVIEW's write — either or both may fire).
- GIT (both variants) calls `--check-phase spec --threshold 1` and
  `--check-phase audit --threshold 1` for T2/T2-RISK/T3/T3-RISK when audit is
  in the required phase set, plus `--check-phase plan --threshold 1` when
  plan is in the required set, deriving that set from the active routing
  profile + the `-RISK` phase-set bump per the section above.
- The spec-gate and plan-gate `--write-evidence` calls (there is no dedicated
  brainstorming/planning skill in this kit) are a CLAUDE.md-level habit — see
  `claude-md-block.md` — not a call from a shipped skill file.
