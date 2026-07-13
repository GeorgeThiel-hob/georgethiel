# Rigor profile: LIGHT

Selected when the interview's resolution algorithm (`interview/INTERVIEW.md`) resolves
to LIGHT — the base case for a **skills-only** Q1 answer with no risk bump (Q4) and no
PII gate (Q5 = no). `START-HERE.md` step 5 reads exactly one rigor manifest; this is the
file it reads when that resolution lands here.

## What LIGHT is for

A Claude Code skill or a small piece of reusable instruction-following content — no
persistent app, no database, no scheduled execution of its own. Process weight beyond
fixture testing would be pure overhead for a deliverable this size.

## Module set (complete, not a delta)

| Module | Condition | Parameters |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | only when interview Q6 = yes | `verification: fixture-testing-only` |

That is the entire installed set at LIGHT. **LIGHT installs no hooks** — there is no
`10-hooks-base`, no `20-tier-system`, no `21-pipeline-skills` in the union this profile
contributes. A skills-only deliverable has no persistent process for a hook to attach
to, and no tier ladder or pipeline skill has anything to gate.

## Deliberately absent

> Hooks, tiers, pipelines — process weight a skills project can't justify.

Verification at this profile is fixture testing only (`24-skill-delivery`'s
`verification: fixture-testing-only` parameter, when that module is in the union) — not
a hook-enforced gate, not a tier ladder, not a pipeline skill's audit loop. There is
nothing in this profile's set for those mechanisms to attach to.

## PII interaction

**Not offered when Q5 (PII) = yes.** The interview's PII gate (`interview/INTERVIEW.md`
Step 4.6 — "PII gate, in full") hard-floors the resolved rigor at STANDARD whenever Q5 is
answered yes; LIGHT is removed from the resolution entirely for that project, with no
override. Do not restate the floor rule here — read it from the interview file, which is
the single source of truth for the resolution algorithm.

## Cumulative note

STANDARD's module set is this profile's set **plus** additions (see
`rigor-STANDARD.md`) — it never drops anything LIGHT installs. FULL's set is STANDARD's
set plus further additions. Module lists only grow going up the rigor ladder.
