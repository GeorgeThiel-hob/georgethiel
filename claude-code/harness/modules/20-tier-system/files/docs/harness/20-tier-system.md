# Harness detail — tier classification, standing briefs, plan-by-reference

Full tier tables and rationale for the tier-classification hard rule summarized in
CLAUDE.md's tier-system block. Read this before treating tier classification as a
formality — the tier decides how much process weight a change gets, and getting
it wrong in either direction has a cost: too low, and a risky change ships
under-reviewed; too high, and a trivial change drags a full pipeline behind it.

## Step 0 of every session: classify the tier

Before starting any work, ask: **"Can this change cause irreversible harm, data
loss, or break other systems?"** The answer sets the tier, and the tier sets the
pipeline. When in doubt, classify one tier up — the cost of over-classifying a
small change is a few extra minutes of process; the cost of under-classifying a
risky one is a shipped defect with no review trail.

Two tables follow: **LITE** (installed at the STANDARD rigor profile — T1/T2
only) and **FULL** (installed at the FULL rigor profile — T1/T2/T3). Read
whichever one matches your install's rigor profile; `START-HERE.md` names which
profile was selected. A profile never has both tables active at once.

---

## LITE variant (STANDARD profile)

| Tier | Criteria | Pipeline |
|------|----------|----------|
| **T1 — Micro** | No logic change, small diff, docs/config/test-only | Fix → safety gate → test → commit → ship |
| **T2 — Standard** | Single-concern feature, bounded scope | Brainstorm+Spec → Plan → Implement → Audit (single round) → ship |
| **T2-RISK** | T2 + path edit matches this install's `RISK_PREFIXES` | T2 pipeline + a re-verify-the-tier-scope check before continuing |

**No T3 row at this profile.** `tier_detection.py`'s `effective_tier` still fails
any unrecognized/typo'd declared tier safe to T2 — there is no tier below T2 that
a RISK-path diff can silently hide behind. If a change is big enough to feel like
it needs T3's heavier pipeline, that is itself a signal to raise the rigor
profile, not to force it through LITE's T2 pipeline.

---

## FULL variant (FULL profile)

| Tier | Criteria | Pipeline |
|------|----------|----------|
| **T1 — Micro** | No logic change, small diff, docs/config/test-only | Fix → safety gate → test → commit → ship |
| **T2 — Standard** | Single-concern feature, bounded scope | Brainstorm+Spec → Plan → Implement → Audit (loop to zero blocking findings) → ship |
| **T2-RISK** | T2 + path edit matches this install's `RISK_PREFIXES` | T2 pipeline + a re-verify-the-tier-scope check before continuing |
| **T3 — Critical** | Multi-system change, schema change, or any change whose failure mode compounds silently over time | Tickets → Brainstorm+Spec → Plan → Implement → Audit (loop to zero blocking findings) → ship → project-update report |
| **T3-RISK** | T3 + path edit matches this install's `RISK_PREFIXES` | T3 pipeline + a re-verify-the-tier-scope check before continuing |

The FULL profile also turns on the MAP effect-chain verification loop at the
spec→plan boundary for every T2/T3 ticket (module 21's `map_mandatory: true`),
and requires the audit loop to reach zero blocking findings rather than a single
round. See module 21's pipeline-skill docs for the exact skill names and commands
your install provides.

---

## `RISK_PREFIXES` — the divergence check

`tier_detection.py` ships with `RISK_PREFIXES: tuple[str, ...] = ()` by default —
inert until the adopter fills it in with their own list of "touches something
hard to undo" path prefixes (a schema/migrations directory, a payments or auth
module, a production config file — whatever carries outsized blast radius in
this project). An empty tuple is a legitimate, permanent choice for a project
with no such paths; it is not a placeholder that must be filled before the
module is considered installed correctly.

Once populated, any diff that touches a `RISK_PREFIXES` path auto-promotes the
ticket's declared tier to its `-RISK` variant (T1 diffs floor to T2-RISK — there
is no such thing as T1-RISK, since a change with this kind of blast radius never
qualifies as micro). The check is a **divergence detector**, not a classifier at
session start: the author declares a tier in the standing brief; this check
verifies the real diff didn't silently exceed it, and blocks with a
re-verify-the-tier-scope instruction if it did.

## Standing briefs and plan-by-reference

The same module ships two more checks, both gating subagent dispatches during
the execute phase:

- **Standing brief (`require_standing_brief`).** Before the first subagent
  dispatch on a feature branch, write a standing brief to
  `docs/superpowers/briefs/<branch-slug>.md`. At the STANDARD profile, one line
  suffices (branch + declared tier is enough for the divergence check to have
  something to compare against). At the FULL profile, use the full brief shape:
  branch, tier, MAP-dossier path (if this ticket ran MAP), and a short
  acceptance-criteria summary. The dispatcher asks for one if it's absent — this
  documented step is why that ask is an expected part of the flow, not a
  surprise block.
- **Plan-by-reference (`check_plan_by_reference`).** A subagent dispatch whose
  prompt looks like an inlined plan-task body (long prompt, checklist markers,
  no line-range citation) is blocked in favor of "Read lines X-Y of
  `docs/superpowers/plans/<plan>.md` and implement that task." This keeps plan
  content on disk, read directly by the subagent that needs it, instead of
  duplicated into every dispatch prompt.

Both checks fail open on any I/O or git error — a mis-firing gate must never
wedge a live subagent dispatch.
