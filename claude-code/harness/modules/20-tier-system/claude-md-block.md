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

Every `Agent`/`Task` dispatch LEADS its prompt with a `[seat:<name>]` tag (or
carries it in `description`) AND passes an explicit `model` on that seat's
allow-list — seats and allowed models: `.claude/state/seat-table.json`. A blocked
dispatch means FIX THE DISPATCH (add the tag + an allowed model); do NOT route
around the gate by doing the work inline in the main conversation — inline work
on the orchestrator's model is the exact token spend the seat table exists to
prevent. Retrieval-grade lookups (file search, grep, git reads) go to
`[seat:retrieval]` subagents. (Honest limit: no hook can force delegation — this
rule makes inline avoidance a visible convention violation, not an impossibility.)

Full tier tables: `docs/harness/20-tier-system.md`.
