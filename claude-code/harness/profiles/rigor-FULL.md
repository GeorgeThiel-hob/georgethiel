# Rigor profile: FULL

Selected when the interview's resolution algorithm (`interview/INTERVIEW.md`) resolves
to FULL — the base case for a **code-heavy** Q1 answer, or a lower-rigor deliverable
pushed here by the risk bump (Q4 fires) or the PII floor (Q5 = yes) reaching the top of
the ladder, including the owner-pinned cell (Q1=LIGHT, Q4 fires, Q5=yes) → FULL.
`START-HERE.md` step 5 reads exactly one rigor manifest; this is the file it reads when
that resolution lands here.

## What FULL is for

A persistent application, service, or pipeline with real users or a database and an
ongoing maintenance surface — or any deliverable whose blast radius (Q4) or data
sensitivity (Q5) compounds enough to warrant the ladder's maximum protection.

## Module set (complete list — supersets STANDARD; inlined here so one read suffices)

The full installed set at FULL, listed directly (no need to also open
`rigor-STANDARD.md` or `rigor-LIGHT.md` — everything they install is repeated here
verbatim):

| Module | Condition | Parameters |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | only when interview Q6 = yes | `verification: fixture-testing-only` |
| `10-hooks-base` | always | — |
| `20-tier-system` | always | `tier_scope: FULL` (T1/T2/T3 — overridden from STANDARD's `LITE`) |
| `21-pipeline-skills` | always | `pipeline: brainstorm→spec→implement`, `audit_rounds: 3` (T3 cap: 5 — see REVIEW variant docs), `audit_variant: full`, `ship_variant: <per Q3>`, `map_mandatory: true`, `pm_reports: true` |
| `22-second-opinion-seat` | always | — (gate-evidence enforcement is uniform across rigor profiles — see module 22 docs; STANDARD and FULL both ship the same blocking phase-evidence gate) |
| `25-ticketing` | always | — |
| `26-code-discipline` | always | — |
| `23-guards` | newly added at FULL | — |

Two parameters this profile requires **verbatim**, per AC-4:

- **MAP at spec→plan** — module 21's tier system requires a MAP pass at the spec→plan
  boundary for every T2/T3 ticket (`map_mandatory: true`). This is the feature
  `rigor-STANDARD.md`'s `map_mandatory: false` gates off; FULL turns it on.
- **Full REVIEW loop (exit at zero P0/P1)** — module 21's audit variant runs to
  completion only when the round produces P0=0 AND P1=0 (`audit_variant: full`). This
  replaces STANDARD's single-round `audit_variant: lite`.

Standing briefs and the token-economy parameters are **FULL-only** — neither
`rigor-LIGHT.md` nor `rigor-STANDARD.md` sets them:

- `standing_briefs: true`
- `plan_by_reference: true`
- `haiku_batching: true`
- `context_offload: true`

Context reset at the spec→execute boundary + per-task-reviewer model tier
scaled to diff size (reference only — the operative copy lives in the
installed CLAUDE.md `## Workflow` span, assembled from
`modules/00-core/workflow-table-FULL.md`; this file is never read by
`installer.py`).

## Deliberately absent

> —

Nothing is deliberately absent at FULL (spec §6). Every gate a lower rigor tier turns
off — the T3 tier, MAP-mandatory, the guard pack — is turned on here, and `23-guards`
enters the module union for the first time.

## Provenance note

This profile's set supersets STANDARD's (and therefore LIGHT's) — every module STANDARD
and LIGHT install is still installed here, inlined above so this file is self-contained
on its own. FULL is the top of the rigor ladder; there is no higher profile for it to be
a delta against, and — unlike STANDARD, which supersets LIGHT — there is nothing above
FULL left to inline from.
