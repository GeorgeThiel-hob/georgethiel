Each session classifies a tier first (module `20-tier-system`, Step 0): **T1** = fix →
safety gate → test → commit → ship; **T2/T3** = brainstorm+spec → plan → implement →
REVIEW → ship, plus MAP at the spec→plan boundary (mandatory at this FULL profile); T3
additionally runs REPORT after shipping. A `-RISK` suffix (module 20's divergence check)
auto-promotes the tier when a diff touches a `RISK_PREFIXES` path. Full tables:
`docs/harness/20-tier-system.md`; full pipeline detail: `docs/harness/21-pipeline-skills.md`.

Context resets at the spec→execute boundary: the standing brief, plan, and MAP
dossier already on disk are the full handoff, so implement starts a fresh
session instead of carrying the spec/MAP conversation forward. Per-task
reviewer dispatches during implement scale model tier to diff size — a small,
mechanical diff routes to a mid-tier model; a subtle or risk-touching diff
routes to the strongest tier this routing profile affords. The whole-branch
REVIEW seat is unaffected by this scaling and keeps its routing-profile-pinned
model at every gate (module `21-pipeline-skills`).
