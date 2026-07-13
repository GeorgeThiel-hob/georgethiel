# Rigor profile: STANDARD

Selected when the interview's resolution algorithm (`interview/INTERVIEW.md`) resolves
to STANDARD — the base case for a **mechanical-automation** Q1 answer, or a
**skills-only** Q1 answer promoted by the risk bump (Q4 fires) or the PII floor (Q5 =
yes). `START-HERE.md` step 5 reads exactly one rigor manifest; this is the file it reads
when that resolution lands here.

## What STANDARD is for

A scripted or no-code automation that runs on a trigger or schedule, touching files or
other systems, but with no user-facing app or database of its own — or a lower-rigor
deliverable whose failure mode (Q4) or data sensitivity (Q5) earns it more
process-verification depth than LIGHT provides.

## Module set (complete list — supersets LIGHT; inlined here so one read suffices)

The full installed set at STANDARD, listed directly (no need to also open
`rigor-LIGHT.md` — everything LIGHT installs is repeated here verbatim):

| Module | Condition | Parameters |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | only when interview Q6 = yes | `verification: fixture-testing-only` |
| `10-hooks-base` | always | — |
| `20-tier-system` | always | `tier_scope: LITE` (T1/T2 only — no T3) |
| `21-pipeline-skills` | always | `pipeline: brainstorm→spec→implement`, `audit_rounds: 1`, `audit_variant: lite`, `ship_variant: <per Q3>`, `map_mandatory: false` |
| `22-second-opinion-seat` | always | — (gate-evidence enforcement is uniform across rigor profiles — see module 22 docs; STANDARD and FULL both ship the same blocking phase-evidence gate) |
| `25-ticketing` | always | — |
| `26-code-discipline` | always | — |

`23-guards` is **not** in this profile's union — see the deliberately-absent list below.

## Deliberately absent

> T3, MAP-mandatory, guard pack.

These features are gated OFF by this profile's manifest parameters and
`claude-md-block` content, **not** by omitting a file — module 21's files copy whole at
every rigor level (AC-4's "module set AND parameters" requirement). The parameter that
gates each one:

| Absent feature | Gated OFF by | Effect |
|---|---|---|
| T3 tier | `20-tier-system`'s `tier_scope: LITE` | Blocks T3 — only T1/T2 are reachable |
| MAP-mandatory | `21-pipeline-skills`'s `map_mandatory: false` | MAP is not required at the spec→plan boundary |
| Guard pack | `guards_installed: false` | `23-guards` is not in the module union at STANDARD |

Module 22's phase-evidence gate is **not** on this list — it is a blocking gate at
STANDARD, same as at FULL. Nothing in the kit reads a rigor-conditional "advisory"
flag for module 22; only the per-routing-profile evidence threshold (PRO/MAX5/MAX20)
varies, not the gate/no-gate behavior.

## Provenance note

This profile's set supersets LIGHT's — every module LIGHT installs is still installed
here (inlined above, not left as a cross-reference). FULL's set (`rigor-FULL.md`)
supersets this one in turn, with further additions inlined there the same way,
overriding `tier_scope` to `FULL` and flipping `map_mandatory` / `guards_installed` on.
Module lists only grow going up the rigor ladder; a higher tier never drops a module a
lower tier installed.
