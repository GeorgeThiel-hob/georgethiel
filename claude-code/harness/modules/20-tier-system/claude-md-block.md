### Tier classification (20-tier-system)

Tier classification is Step 0 of every session: T1 = micro (docs/config/test-only
changes), T2 = standard feature, T3 = critical (strategy/schema/multi-system —
FULL profile only). A `-RISK` suffix (this module's divergence check)
auto-promotes a ticket's declared tier when a diff touches a `RISK_PREFIXES`
path.

Before your first subagent dispatch on a feature branch, write a standing brief
to `docs/superpowers/briefs/<branch-slug>.md` — one line suffices at STANDARD;
the FULL profile uses the full Rule-8 brief (branch, tier, MAP-dossier path,
acceptance criteria). The dispatcher asks for one if it is absent — this
documented step is why that gate is an expected prompt, not a surprise block.

Full tier tables: `docs/harness/20-tier-system.md`.
