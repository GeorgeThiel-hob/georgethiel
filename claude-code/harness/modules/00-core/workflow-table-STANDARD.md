Each session classifies a tier first (module `20-tier-system`, Step 0): **T1** = fix →
safety gate → test → commit → ship; **T2** = brainstorm+spec → plan → implement → REVIEW
→ ship. This profile does not install T3 (`tier_scope: LITE`) or the MAP spec→plan gate
(`map_mandatory: false`) — see `rigor-STANDARD.md`. A `-RISK` suffix (module 20's
divergence check) auto-promotes the tier when a diff touches a `RISK_PREFIXES` path. Full
tables: `docs/harness/20-tier-system.md`; full pipeline detail:
`docs/harness/21-pipeline-skills.md`.
