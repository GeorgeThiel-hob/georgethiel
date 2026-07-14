# Harness detail — the pipeline skills (REVIEW, MAP, GIT, REPORT)

Full delta list and rationale for the four-skill pipeline summarized in
CLAUDE.md's pipeline block. Read this before treating any of the four skills as
a verbatim copy of a generic template — each was scrubbed from a specific
source with specific, named deltas, and this doc is where those deltas are
recorded in full.

## Why four skills, why two have variants

REVIEW and GIT vary because they sit on the two axes this kit's interview asks
about directly: REVIEW's variant follows the **rigor** answer (how much
process-verification depth a change needs — single-pass at STANDARD, a
round-capped loop to zero blocking findings at FULL), and GIT's variant follows
the **ship-target** answer (does code reach the default branch through a GitHub
remote, or entirely on the local machine). Both are genuine either/or forks in
*mechanism* that the interview already resolves before install, so shipping
both variants and selecting one at copy time is cheaper and safer than trying
to write one file that branches at runtime.

MAP and REPORT don't vary, because what a profile changes about them is *whether
they run*, not *how* they work. MAP's mechanism (Step 0 seed, a fixed two-round
budget with a single reopen round, oscillation guard) is identical whether it's
mandatory (FULL, `map_mandatory: true`) or simply unused (STANDARD,
`map_mandatory: false`) — the
rigor profile toggles a parameter that governs *when this project requires it*,
not the loop itself. Same for REPORT: whether a ticket reaches REPORT's "T3 Critical
pipeline" trigger depends entirely on whether T3 exists at this rigor profile
(it doesn't, at STANDARD) — REPORT's own content never needs to know or branch on
that; the tier ladder above it already gates the trigger.

## MAP — full delta list

Source: `.claude/skills/MAP/SKILL.md`. Kit dest: `MAP/SKILL.md` (no variant
split).

1. **Routing-directive-name strip.** The source cites a specific internal
   model-routing directive by name, with a superseded-directive history and specific dates.
   The kit variant states only the current policy — dispatch the
   strongest-available adversarial-review seat (the same "Audit reviewer" seat
   REVIEW uses, per the active routing profile) for all code-reading and
   adversarial roles — with zero surviving reference to the retired directive's
   name, date, or the project-specific opinion that motivated it.
2. **Coefficient-example strip.** The blindspot-class list's
   "coefficient-vs-intuition" illustration cited a specific fitted-parameter
   collapse from a pattern-source project's own calibration work. Replaced with a
   domain-neutral illustration of the identical rhetorical point: a regression
   coefficient collapsing to a degenerate constant, read as "no effect" without
   checking why the fit degenerated.
3. **Environment-pair strip.** The "inferred-dependency" illustration cited two
   specific named database files from the pattern-source project. Replaced with a
   generic staging-vs-production conflation example (treating "this ran against
   staging" as proof it holds for production, when the two diverge).
4. **Dossier-lore strip (partially superseded by the C1 budget rewrite,
   item 9 below).** Three separate citations of past incidents by specific
   date or ticket ID (a mislabeled-then-corrected node, a circularity-rejection
   convention's ticket ID, an observe-only tally feature's ticket ID) are
   generalized to describe the underlying failure MODE or convention, with the
   specific date/ticket-ID removed. None of the three lessons need the
   incident history to teach the point. A fourth citation — an incident about
   escalating purely because a round count was reached — no longer survives
   in any form: the fixed round budget in item 9 below removes that judgment
   call entirely. A round past the budget is never a self-judgment call, only
   an escalation, so there is nothing left of that incident to generalize.
5. **Dossier filename rename.** The source's dossier artifact filename is
   itself one of this kit's deny-listed literal tokens (it names a specific
   internal convention, not a generic term). The kit variant renames it to
   `map-dossier.md` (3 occurrences), consistent with the `**MAP-dossier:**`
   pointer-field naming the file already used elsewhere in the source text.
   The directory convention, `docs/analyses/<investigation-slug>/`, is
   unchanged — it's a plain directory-naming pattern, not deny-listed and not
   project-specific.
6. **Gate-evidence CLI rewrite.** The source's sentinel-writing CLI
   invocation is rewritten to module `22-second-opinion-seat`'s
   `check_gate_evidence.py --write-evidence audit`.
7. **Conditional-dependency honesty (module 23-guards).** Two source features —
   the observe-only blindspot tally and the circularity-rejection WARN on the
   dossier's `ev:` slot — depend on hook infrastructure (`claim_detector.py`,
   `circularity_guard.py`) that ships only with module `23-guards`, which is
   FULL-profile-only. The kit variant states each as "only if module 23-guards
   is present," skipping cleanly at STANDARD, while keeping the underlying RULE
   (never cite a prior dossier as primary evidence) in force regardless of
   whether the automated check exists to catch a violation.
8. **"the bot" → "the system"**, throughout the description and body — this
   kit maps effect-chains in any kind of project, not one specific kind of
   application.
9. **C1 budget rewrite (2026-07-14, KIT-LEAN-FULL-01).** The source's
   convergence rule was originally open-ended: each round expanded the map one
   layer outward from the finding and the loop would not stop until an entire
   round surfaced nothing new, with no ceiling on how many rounds that could
   take. Field data showed the later rounds reliably caught only cosmetic
   issues, so the rule was replaced with a fixed budget: a first adversarial
   round is handed the complete surface up front (rather than discovering it
   one layer at a time), a second fresh-eyes round independently re-examines
   the first round's conclusions, and at most one further round is allowed to
   verify a fix for a genuine defect found late — anything past that is never
   a self-judgment call, only an escalation to a human. Cosmetic/minor
   findings fold in immediately at any point and never consume that budget.
   This is a substantive behavior change, not a scrub — recorded here per this
   doc's charter (see the intro) rather than skipped as cosmetic.

## REPORT — full delta list

Source: `.claude/skills/PM/SKILL.md`. Kit dest: `REPORT/SKILL.md` (no variant
split).

1. **Post-deploy hard-gate strip.** The source's entire "Pre-flight Checks"
   section required a post-deploy-verification marker and artifact before a
   report on the source's most live-execution-adjacent tier could even be
   written. That entire post-deploy-verification mechanism is excluded from
   this kit (`excluded/README.md`) — porting the gate without the mechanism it
   checks would either silently pass (dead check) or permanently block reports
   (wedged check). The whole section is removed; a one-line pointer to the
   excluded-module's write-your-own-gate example replaces it.
2. **Domain-specific status-row strip**, and the rest of that status table (delta 4).
3. **Opt-in-tracking strip.** The source's report template carried a
   per-ticket "opt-in: yes/no" line tracking whether an optional debate-tools
   session was used, feeding a project-specific measurement scheme for whether
   that demotion was safe. The line and the "When to Use" bullet that named the
   underlying tools are both removed; the trigger bullet is generalized to a
   plain cross-reference to module `31-debate-tools` by module name (module
   names are kit-legitimate and not deny-listed; the specific opt-in-tracking
   convention is this-project-specific and does not travel).
4. **Status table genericized.** Beyond delta 2's status row, the entire
   source status table (domain-specific operational rows) assumed one specific kind of
   project. It's replaced with an illustrative "adjust rows to whatever
   operational metrics matter for this project" table, since a fixed generic
   schema would just trade one project's specific metrics for another's.
5. **Remaining domain residue.** "the bot" → "the system" throughout;
   stack-specific commands (`pytest`) → `{{TEST_CMD}}` (module `00-core`);
   a specific project's config-file path → generic "central config file, if
   any"; `gh issue view <number>` → cross-referenced to both of module
   `25-ticketing`'s variants (GitHub issues, local `tickets/` folder);
   `analysis/results/` or similar → generic "wherever this project
   keeps generated artifacts"; the writing-style paragraph's specific,
   domain-tailored audience description →
   "a technically sharp reader who is not necessarily a specialist in this
   project's domain."

## REVIEW — full delta list (both variants)

Source: `.claude/skills/AUDIT/SKILL.md`. Kit dest: `REVIEW/SKILL-lite.md` +
`REVIEW/SKILL-full.md`.

Shared deltas (applied to the base text before branching into lite/full):

1. **Gate-evidence rewrite** — both sentinel-writing CLI invocations (the
   post-fix re-verify write at what was source `:228`, and the clean-pass write
   at what was source `:270`) → module 22's
   `check_gate_evidence.py --write-evidence <phase>`.
2. **`RISK_PREFIXES` rewrite** — every hard-coded critical-path literal (three
   source-directory prefixes plus a settings filename, all specific to the
   pattern source's own layout) across the T1 safety gate, the fix-routing rule,
   the TODO report line, and the TODO-debt ceiling → this install's
   `RISK_PREFIXES` (module 20).
3. **Domain-example rewrite** — the severity table's P0 example, the P1
   definition's severity-impact phrase, and the Tier-Reclassification bullet's
   T3-indicator text were all domain-specific illustrations; the kit variant
   reads "Off-by-one in a core calculation" (P0), "contained/non-critical
   impact" (P1), and "Core business-logic calculations, algorithm parameters,
   calibration/tuning logic" (Tier-Reclassification).
4. **Seat-routing rewrite.** Every hardcoded model name (the source hard-coded
   Opus for finding generation and high-stakes fixes, Sonnet for the T1 gate
   and ordinary fixes, Haiku for mechanical sub-operations) is rewritten to the
   active routing profile's seat names — Audit reviewer, Workers, Retrieval.
   This one is load-bearing, not cosmetic: a hardcoded "opus" would be flatly
   wrong on a Pro-plan install, whose seat table (`profiles/routing-PRO.md`)
   assigns a different model to the Audit-reviewer role than a Max20x install
   does.
5. **The finding-shape's high-stakes flag renamed** (and its justification
   field) in the audit-finding shape and every routing rule that reads it —
   matching the `RISK_PREFIXES` naming scheme instead of assuming a financial
   domain.
6. **`{{SHARED_CODE_HOME}}` ADAPT token** (new) — the hand-mirror/duplication
   check's remediation-target path named a specific shared-code directory in
   the pattern-source project; the kit variant substitutes this new ADAPT token. Module
   26's optional ratchet-template component, if installed, targets the same
   location, so the two stay in sync without either one hard-depending on the
   other's presence.
7. **Incident-lore strip** — the duplication check's incident-class citation,
   the re-verify gate's motivating-incident sentence, and the entire "Model
   Routing Provenance" section (a historical footnote about a retired
   validation plan that was never run) are all removed. None taught a
   generalizable lesson without the specific history behind them; the
   surviving text states the current rule directly.
8. **ADR-specific bullets dropped, not scrubbed.** The source's Step 2b carried
   two bullets enforcing a CLAUDE.md rule ("write an ADR for load-bearing
   architectural decisions") that isn't part of any kit module's
   `claude-md-block.md` — a business-sensitive-figure deny-list grep over ADR
   docs, and an ADR-presence-on-architectural-change check, plus the
   `Override:`-line escape valve that existed only to dismiss those two. Kept
   scrubbed-but-present, all three would silently check compliance with a
   policy the kit never installs — dropped entirely instead. The remaining
   Step-2b bullets (NO-IMPLEMENTATION/PARTIAL, the new-module deletion test,
   the divergent-interface-shapes check) are unaffected — none of them assume
   the ADR rule exists.

Lite-only reduction (Step 10.4): single-pass review — no round cap, no
re-review loop, no Step-2b spec→code surface diff, no 2b(iii) duplication or
leanness checks, no Step 4b re-verify gate (nothing to re-verify without a
re-audit loop to gate), and no Tier-Reclassification section (this profile's
tier scope, module 20's `tier_scope: LITE`, has no T3 to reclassify into — the
section would be a dead reference to a tier this profile doesn't have).

Full-only additions (Step 10.5): the complete round-capped loop (T2=3/T3=5,
checkpoint not hard stop), the Step-2b spec→code surface diff, Step 2b(ii)'s
effect-chain-per-finding trace, Step 2b(iii)'s hand-mirror/duplication check
(unconditional) and leanness-baseline-bump guard, and Step 4b's mandatory
re-verify gate.

**REVIEW variant dependency note — the 2b(iii)(b) conditionality in full.** The
pattern source's leanness-baseline-bump guard (2b(iii)(b)) keys on two files that exist
only because a specific prior ticket in the pattern-source project built them:
`tests/leanness_baseline.json` and `tests/test_leanness_ratchet.py`. Those two
filenames are generic testing-tooling names (not deny-listed, not
project-specific), so the kit variant keeps them literally — but wraps the
whole sub-check in an explicit conditional: run it only if module
`26-code-discipline`'s optional ratchet-template component was activated (i.e.,
only if the live, non-`.template` versions of those two files actually exist in
this repo — installation alone only places the inert `.template` files). If
the live files don't exist, the sub-check is skipped cleanly, not silently
mis-run against files that don't exist. This is the same "don't wedge on an
absent optional dependency" pattern module 10's dispatcher uses for its
import-guarded checks.

## GIT — full delta list (both variants)

Source: `.claude/skills/GT/SKILL.md`. Kit dest: `GIT/SKILL-github.md` +
`GIT/SKILL-local.md`.

Shared deltas (applied to both variants):

1. **Gate-set rewrite.** The pattern source's single pre-flight call — one bare
   invocation of a pattern-source sentinel-management CLI script — opaquely
   bundled: a missing-brief check keyed on a pattern-source live-path prefix
   constant, a per-tier phase-distribution check (spec + audit required at
   T2/T3, plan additionally at T3), a MAP-dossier
   `Status: CONVERGED` check backed by a transcript-verifiable evidence store,
   and a conditional playbook-slots check. Module 22 (this kit's
   gate-evidence module) ships ONLY the generic "record a call, count calls,
   compare to a threshold" primitive — none of that bundled logic ports as a
   single script. The kit GIT variant therefore documents the reduced gate
   set as explicit steps instead of one opaque call:
   - Per-phase evidence checks (`check_gate_evidence.py --check-phase <phase>
     --threshold 1`) for each phase in the REQUIRED PHASE SET the routing
     profile names for this tier — spec and audit at T2/T3 on MAX5/MAX20,
     spec only at PRO, plus plan for T3 on MAX20 — `audit-fix` evidence counts
     as a substitute for `audit`. The routing profile's number (e.g. MAX5's
     `{T2: 2}`) is a COUNT of required phases, never the `--threshold` value
     itself; every phase check always uses `--threshold 1`.
   - The `-RISK` phase-set bump (adds the next phase in `[spec, audit, plan]`
     not already required, capped at all 3 phases) is computed BY THIS
     SKILL, not by module 22 — matching module 22's own deletion-test note
     that tier semantics belong at the call site, not inside the generic
     evidence module.
   - A MAP-dossier-presence condition, ONLY at the FULL profile
     (`map_mandatory: true`): does the standing brief's `**MAP-dossier:**` path
     exist, and does that file's terminal status line read
     `Status: CONVERGED`? This is a plain Read/Glob check — a transcript-backed
     "a sentinel must be backed by a real tool-call in the transcript"
     mechanism some pattern sources use is explicitly NOT ported (it has no
     equivalent when the second-opinion seat is a subagent rather than a
     built-in tool; see module 22's own enforcement-strength honesty rule).
   - The playbook-slots check, ONLY when module `30-reasoning-playbooks` is
     installed — always WARN-only, never blocking.
   - Override-log path renamed from a pattern-source sentinel-store directory to
     `.claude/state/gate-evidence/<branch-slug>/overrides.log`.
2. **`RISK_PREFIXES` rewrite** — a pattern-source live-path prefix constant (the
   T1-auto-pass condition, the missing-brief condition) → `RISK_PREFIXES`,
   matching module 20's tier-suffix naming.
3. **Lint/type step de-scripted.** The source's changed-file-scoped lint gate
   shells out to a project-specific Python script running ruff/black/mypy over
   `src/`+`tests/` — no kit module ships that script, and it assumes a Python
   stack. The kit variant describes the same changed-file-scoped principle
   (a pre-existing error in an untouched file doesn't block; touching a file
   makes its errors blocking too) using this project's own `{{LINT_CMD}}` /
   `{{TYPE_CMD}}` tokens (module `00-core`) instead of a nonexistent script.

Local-variant addition (Step 10.8, the adaptation): see the module README's
"GIT-local adaptation" section for the full rationale. In short: steps 1-3 of
the source (push, create PR, merge PR) collapse into one local squash-merge
step (`git merge --squash` + `git commit`), with no remote command anywhere in
the file.

## Kit tier model

T1/T2/T3, with an optional `-RISK` suffix from module 20's divergence check
(the kit's generalization of a similar pattern-source risk-tier suffix). A
`-RISK` suffix adds one more phase to module 22's gate-evidence required phase
set — the next phase in `[spec, audit, plan]` not already required for that
tier, capped at all 3 phases — over the active routing profile's base phase
set for that tier — mirroring a base+1 escalation pattern, expressed as a
phase-set expansion rather than a threshold increment — and nothing else.
There is no kit-shipped equivalent of a pattern-source post-deploy verification
gate: that entire mechanism stays in `excluded/README.md` as the
"here's what a domain-specific gate looks like, write your own" worked example,
because it depends on knowing what "deployed" even means for a given project
(a server restart, a container rollout, a published package) in a way this kit
cannot generalize.
