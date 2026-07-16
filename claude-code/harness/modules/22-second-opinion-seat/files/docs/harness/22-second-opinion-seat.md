# Harness detail — the second-opinion-seat gate-evidence mechanism

Full seat-dispatch instructions and the gate-evidence primitive's threshold
rules, summarized in CLAUDE.md's `22-second-opinion-seat` block. Read this
before treating the ship-time gate-evidence check as an opaque pass/fail —
the mechanism it enforces is a *convention* (write a marker before a call,
count markers at ship time), not a guarantee that the call itself happened
with any particular rigor. The Enforcement honesty section below says this
plainly.

## What the second-opinion seat is

[seat:second_opinion] "The advisor tool if this environment has one, else a fresh-context subagent
on the strongest affordable model." An advisor-tool-shaped capability is an
environment fact, not a platform guarantee: some accounts and sessions have
it, some don't, and no seat assignment can force it into existence. The
load-bearing property is **fresh context** — a reviewer that did not produce
the work under review — not model tier. Model tier is a multiplier on top of
that property, never a substitute for it. (Same framing as
`profiles/routing-PRO.md`'s "The second-opinion seat is a capability, not a
platform guarantee" section — read that file for the full seat table.)

## The gate-evidence primitive

`check_gate_evidence.py` (backed by `lib/gate_evidence.py`) is a two-verb CLI:

```
python3 .claude/hooks/check_gate_evidence.py --write-evidence <phase>
python3 .claude/hooks/check_gate_evidence.py --check-phase <phase> --threshold <N>
```

`--write-evidence <phase>` writes one marker file under
`.claude/state/gate-evidence/<branch-slug>/evidence-NNN-<phase>.touch`,
called BEFORE the second-opinion-seat call it records, not after — the
marker means "a call for this phase is about to happen / has happened," and
recording it early means a call that gets interrupted mid-flow still leaves
a trace. `--check-phase <phase> --threshold <N>` counts markers tagged with
`<phase>` and passes iff the count meets `<N>`; `<N>` is always supplied by
the calling skill, never hardcoded inside this module (see "Thresholds are a
routing-profile parameter" below).

**The `audit`/`audit-fix` substitution.** When checking `phase == "audit"`,
evidence recorded under `"audit-fix"` also counts toward the total. Module
`21-pipeline-skills`' REVIEW variant writes `audit-fix` at its post-fix
re-verify gate (Step 4b) and `audit` on a clean Step-6 report; MAP also
writes `audit` at its own post-loop second-opinion synthesis step when MAP is
the convergence engine for a ticket. All three writers are idempotent with
each other, and the ship check (module 21's GIT variants,
`--check-phase audit --threshold <N>`) accepts evidence from any combination
of them — a ticket that only ever needed a fix-then-reverify pass is not
penalized for never separately recording a bare `audit` marker.

**Directory layout:**

```
.claude/state/gate-evidence/<branch-slug>/
  evidence-001-spec.touch
  evidence-002-audit.touch
  overrides.log
```

`overrides.log` lives alongside the evidence markers but is written directly
by module 21's GIT skill variants (the logged-override escape hatch when a
gate is short), never by this module's own code:

```json
{"ts": "<iso8601>", "branch": "<slug>", "tier": "T2", "phase": "audit", "count": 0, "threshold": 1, "reason": "<user text>"}
```

## Seat-dispatch instructions per routing profile

The number and placement of second-opinion-seat calls a ticket needs scales
with the installed routing profile — a Pro-plan account cannot afford the
same call volume a Max-20x account can. **This table mirrors the
authoritative numbers in `profiles/routing-{PRO,MAX5,MAX20}.md`'s own
"Sentinel gate-count for this profile" sections — read those files as the
source of truth, not this restatement, if the two ever appear to disagree.**

| Profile | Gates that need a call | Required-phase-gate count `{T2, T3}` |
|---|---|---|
| **PRO** | Spec gate only, ONE call/ticket | `{T2: 1, T3: 1}` |
| **MAX5** | Spec gate + audit gate | `{T2: 2, T3: 2}` |
| **MAX20** | Every gate (spec, plan, audit) | `{T2: 2, T3: 3}` |

The number in the third column is a COUNT of distinct phase-gates that each
need their own evidence — NOT a per-phase repeat-count, and never the value
passed as `--threshold`. The calling skill (module 21's GIT variants) derives
the REQUIRED PHASE SET the count names (e.g. MAX5's `{T2: 2}` means "spec AND
audit," one review apiece) and checks each phase in that set at
`--check-phase <phase> --threshold 1`. One review is one piece of evidence
for its own phase; the count says how many distinct phases need a review,
not how many reviews any single phase needs.

- **PRO — 1 call/ticket, at the spec gate only.** The ship check verifies
  the one spec-gate review happened — it catches "skipped review entirely,"
  the realistic Pro failure mode, without demanding call volume a
  flagship-constrained account can't sustain.
- **MAX5 — spec + audit gates.** Two calls per ticket at T2 and T3 alike:
  once at spec approval, once backing the audit clean-pass (or its
  audit-fix substitute).
- **MAX20 — every gate.** Spec and audit at T2; spec, plan, AND audit at T3
  (module 21's GIT variant additionally checks `--check-phase plan` only for
  T3/T3-RISK) — the full per-gate call volume this profile's seat budget
  supports.

## The `-RISK` phase-set bump

Documented here, NOT hardcoded inside `gate_evidence.py`. The CALLING skill
(module 21's GIT variants) derives the required phase SET (not a bare count)
from (routing profile, tier), then — if the tier carries a `-RISK` suffix —
adds the NEXT phase in the sequence `[spec, audit, plan]` not already in the
set, capped at all 3 phases:

```
required_phases = routing_profile_phase_set(profile, tier)
if tier.endswith("-RISK"):
    for phase in ["spec", "audit", "plan"]:
        if phase not in required_phases:
            required_phases.add(phase)
            break  # add exactly one phase; the loop is a no-op once at the 3-phase cap
```

— higher-consequence (`-RISK`) tickets raise the required-phase count by
one, mirroring a base+1 escalation pattern, expressed as a phase-set
expansion rather than a threshold increment (every phase in the resulting set is still checked at
`--threshold 1`, never at a bumped number). Worked examples (MAX5 profile,
`{T2: 2, T3: 2}` base — i.e. `{spec, audit}` at both tiers):

| Tier | Base phase set | `-RISK`? | Required phase set |
|---|---|---|---|
| T2 | `{spec, audit}` | no | `{spec, audit}` |
| T2-RISK | `{spec, audit}` | yes | `{spec, audit, plan}` |
| T3 | `{spec, audit}` | no | `{spec, audit}` |
| T3-RISK | `{spec, audit}` | yes | `{spec, audit, plan}` |

A profile already at the 3-phase cap absorbs the bump with no change — e.g.
MAX20's T3 base set is already `{spec, audit, plan}`, so MAX20-RISK T3 stays
`{spec, audit, plan}`.

**Deletion-test note** (`docs/harness/26-code-discipline.md`): if this logic
lived inside `gate_evidence.py` instead of at the call site, deleting module
`20-tier-system` (the `-RISK` semantics) would leave dead tier-suffix logic
entangled in the generic evidence module. Keeping it at the call site is the
deeper split — module 20 owns tier semantics, module 22 owns evidence
counting, and neither module needs to know the other's internals.

## Enforcement honesty statements

**Sentinel enforcement strength.** When an advisor tool is present, the gate-evidence
check (the sentinel module) is **gate-grade**: it is forge-resistant and
transcript-visible, so the evidence of a gate having run cannot be fabricated. When the
same role is filled by a subagent seat instead, the check is a **WARN-grade convention**
that the orchestrator could forge. The kit says this plainly rather than claiming
gate-grade enforcement in a configuration that only supports a convention.

This statement is worded identically to `START-HERE.md`'s "Enforcement
honesty statements" section and to every `profiles/routing-*.md` file's own
copy — read any of the three, they say the same thing. Practically: on a
subagent-seat install, a `.touch` marker file proves a write happened, not
that the second-opinion call behind it was genuine or substantive. The
gate-evidence check is a convention the orchestrator is trusted to follow,
not a mechanism that can catch an orchestrator that skips the call and
writes the marker anyway. Tell the member this plainly rather than
overselling what the check can catch.
