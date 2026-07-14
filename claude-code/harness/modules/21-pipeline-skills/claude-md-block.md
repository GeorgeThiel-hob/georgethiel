### Pipeline (21-pipeline-skills)

Per tier: **T1** = fix → safety gate → test → commit → ship (GIT). **T2/T3** =
brainstorm+spec → plan → implement → REVIEW → ship (GIT), plus MAP at the
spec→plan boundary (FULL profile only, `map_mandatory: true`); **T3**
additionally runs REPORT after shipping.

Tiers carry an optional `-RISK` suffix (module `20-tier-system`'s divergence
check, fired when a diff touches a `RISK_PREFIXES` path). A `-RISK` suffix adds
one more phase to the second-opinion gate-evidence required phase set (module
`22-second-opinion-seat`) — the next phase in `[spec, audit, plan]` not
already required for that tier, capped at all 3 phases — and nothing else —
there is no separate post-deploy verification step in this kit. If your
project needs one (e.g. a change that only takes effect after a separate deploy
step), that's a domain-specific extension — see `excluded/README.md`'s
write-your-own-gate example.

REVIEW ships in two variants (lite at STANDARD, full at FULL); GIT ships in two
variants (github, local) selected at install by how code reaches your default
branch. Full skill deltas + the kit tier model:
`docs/harness/21-pipeline-skills.md`.

Per-task reviews during implement are risk-scoped, not universal: dispatch one
ONLY for a task that touches a `RISK_PREFIXES` path or introduces non-trivial
logic — new behavior, branching, state, or a cross-file interface. A task that
is docs/config/tests-only, or a mechanical transcription of already-reviewed
content, skips the per-task review and goes straight to the whole-branch
REVIEW instead. This is a FULL-profile leanness rule: an unscoped per-task
review taxes every task at 1-2 extra reviewer dispatches for no added catch
rate on that class of task.
