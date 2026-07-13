Each session classifies a tier first (module `20-tier-system`, Step 0): **T1** = fix →
safety gate → test → commit → ship; **T2/T3** = brainstorm+spec → plan → implement →
REVIEW → ship, plus MAP at the spec→plan boundary (mandatory at this FULL profile); T3
additionally runs REPORT after shipping. A `-RISK` suffix (module 20's divergence check)
auto-promotes the tier when a diff touches a `RISK_PREFIXES` path. Full tables:
`docs/harness/20-tier-system.md`; full pipeline detail: `docs/harness/21-pipeline-skills.md`.
