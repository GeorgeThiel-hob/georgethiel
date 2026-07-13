# Module 21 — pipeline-skills

**Purpose:** the 4-skill ticket pipeline: brainstorm→spec→plan→implement→**REVIEW**→
ship (**GIT**), plus **MAP** for verification loops at the spec→plan boundary and
**REPORT** for post-ticket milestone reports. This module ships the four skills that
give the tier system (module `20-tier-system`) something to actually run —
without it, a declared tier has no review loop, no ship gate, and no report
format behind it.

Two of the four skills ship as **flag-selected variant pairs** — the installer
resolves the flag BEFORE copying and copies exactly one variant per destination
path, renaming away the variant suffix to the literal `SKILL.md`:

- **`REVIEW/SKILL-{lite,full}.md`** — selected by this project's rigor manifest's
  `audit_variant` parameter (`lite` at STANDARD, `full` at FULL).
- **`GIT/SKILL-{github,local}.md`** — selected by the interview's Q3 ("how does
  code reach your default branch?").

`MAP/SKILL.md` and `REPORT/SKILL.md` ship as single files — their *mechanism*, not
their *target*, is what a profile changes (see "Why four skills, why two have
variants" in the detail doc).

## Dependencies

- **`20-tier-system` (required).** Every skill here reads its `RISK_PREFIXES`
  divergence check and its T1/T2/T3(-RISK) tier tables. Module 21 has no tier
  concept of its own.
- **`22-second-opinion-seat` (required).** All four skills reference its
  gate-evidence mechanism (`check_gate_evidence.py`) in place of a
  pattern-source sentinel-management CLI script. REVIEW and MAP additionally use
  its seat-dispatch abstraction (the second-opinion seat: the advisor tool if
  this environment has one, else a fresh-context subagent) wherever the
  pattern-source skills called a bare advisor tool directly.
- **`26-code-discipline` (co-installed at every rigor profile that installs this
  module — STANDARD and FULL both always include it; not itself optional).**
  REVIEW's Step 2b unconditionally cites its `docs/harness/26-code-discipline.md`
  (the deletion test, and the divergent-interface-shapes discipline). Module
  26's own **ratchet-template sub-component**, however, IS optional — REVIEW-full's
  Step 2b(iii)(b) is conditional on whether that sub-component (`tests/
  leanness_baseline.json` + `tests/test_leanness_ratchet.py`) was activated (installation
  alone only places the inert `.template` files; the ratchet engages once those are
  renamed to live files); skip that one sub-check cleanly when it wasn't.
- **`30-reasoning-playbooks` (optional).** Both GIT variants run its
  playbook-slots check only when that module is installed; it is WARN-only
  either way.
- **`23-guards` (optional, FULL-profile-only).** MAP's observe-only blindspot
  tally and the circularity-rejection WARN on its dossier both key on this
  module's presence; MAP states the underlying rule regardless and just skips
  the automated check cleanly when 23 isn't installed (it never ships at
  STANDARD).
- **`31-debate-tools` (optional).** REVIEW's "if the debate-tools module was used
  for this ticket" checklist item and REPORT's "after a multi-agent debate session"
  trigger both cross-reference it by module name, not by its own skill names —
  see the deny-list note below.

ADAPT notes: none unique to this module — `{{RISK_PREFIXES}}` (module 20),
`{{TEST_CMD}}` / `{{LINT_CMD}}` / `{{TYPE_CMD}}` (module 00-core), and
`{{SHARED_CODE_HOME}}` (new — see REVIEW's delta list below) are the only
template tokens these four files use.

## What ships here

- `files/dot-claude/skills/REVIEW/SKILL-lite.md` — scrubbed STANDARD-profile variant.
- `files/dot-claude/skills/REVIEW/SKILL-full.md` — scrubbed FULL-profile variant.
- `files/dot-claude/skills/MAP/SKILL.md` — scrubbed single variant.
- `files/dot-claude/skills/GIT/SKILL-github.md` — scrubbed github-ship variant.
- `files/dot-claude/skills/GIT/SKILL-local.md` — **adaptation** (no
  pattern-source counterpart) for a fully local, no-remote ship path. See
  "GIT-local adaptation" below.
- `files/dot-claude/skills/REPORT/SKILL.md` — scrubbed single variant.
- `files/docs/harness/21-pipeline-skills.md` — full delta list + kit tier model
  + "why four skills, why two have variants" rationale.
- `claude-md-block.md` — the compact CLAUDE.md digest every profile installing
  this module gets.

None of these are verbatim copies (copy-only invariant, satisfied by authoring
the variant once, here, at cut time — the installer still only copies).

## Delta list (AC-6 — every delta named, not just "scrubbed")

### MAP (`.claude/skills/MAP/SKILL.md` → `MAP/SKILL.md`)

1. **Routing-directive-name strip.** Every reference to a specific internal
   model-routing directive by name is generalized to "the strongest-available
   adversarial-review seat" / "the second-opinion seat" wording, with the
   historical routing-change narrative (specific dates, the superseded
   directive's name) removed — the kit states the current policy, not its
   history.
2. **Coefficient-example strip.** The source's project-specific illustration of
   a fitted parameter collapsing to a degenerate value (in the blindspot-class
   list) is replaced with a domain-neutral illustration of the same rhetorical
   point: a regression coefficient collapsing to a degenerate constant, read as
   "no effect" without checking why the fit degenerated.
3. **Environment-pair strip.** The source's illustration of conflating two
   named internal database environments is replaced with a domain-neutral
   staging-vs-production conflation example.
4. **Dossier-lore strip.** Every reference to a specific past incident by date
   or ticket ID (a round-count failure mode, a mislabeled-then-corrected node,
   a circularity-rejection convention citation) is generalized to describe the
   failure MODE itself, with the date/ticket-ID removed.
5. **Dossier-filename rename → `map-dossier.md`.** The source's dossier
   artifact filename is itself one of this kit's deny-listed literals (an
   internal convention name, not a generic term); the kit variant renames the
   artifact (3 occurrences) to `map-dossier.md`, keeping the
   `docs/analyses/<investigation-slug>/` directory convention (a plain
   directory-naming pattern, not itself deny-listed).
6. **Gate-evidence CLI rewrite.** The source's sentinel-writing CLI invocation
   is rewritten to module 22's `check_gate_evidence.py --write-evidence audit`.
7. **Ticket-ID / hook-numbering strip.** A source citation of a project-specific
   ticket ID (for the blindspot-tally feature) and a source citation of a
   project-specific hook-numbering convention (for the standing-brief bypass
   prefix) are both replaced with plain module-name references (module
   `23-guards`, module `20-tier-system`).
8. **"the bot" → "the system"**, throughout (description frontmatter + body) —
   this kit targets any project shape, not only one kind of application.

### REPORT (`.claude/skills/PM/SKILL.md` → `REPORT/SKILL.md`)

1. **Post-deploy hard-gate strip.** The source's entire "Pre-flight Checks"
   section (a gate specific to one live-execution tier, requiring a
   post-deploy-verification marker and artifact) is removed outright — it
   couples to a post-deploy verification mechanism this kit excludes entirely,
   and would be dead-or-wedging in any kit install since no kit module ships
   that mechanism. A one-line pointer to `excluded/README.md`'s
   write-your-own-gate example replaces it.
2. **Domain-specific status row strip.** A row naming this project's
   a domain-specific execution mode is removed from the status-table template
   entirely, along with the rest of that table's domain-specific rows (domain-specific operational rows) — replaced with an
   illustrative, adjust-as-needed example table (see delta 4).
3. **COUNCIL/DEBATE opt-in strip.** Both the report-template opt-in line and
   the "When to Use" bullet naming that same feature by name are removed;
   the "When to Use" bullet is generalized to "after a multi-agent debate
   session (module `31-debate-tools`, if installed)" — a legitimate module-name
   cross-reference, not the specific opt-in-tracking convention (that
   convention doesn't travel with the kit).
4. **Domain-specific status table → illustrative table.** Beyond delta 2, every
   remaining domain-specific row (domain-specific operational rows) is replaced with a short "adjust rows to whatever
   operational metrics matter for this project" example, since the underlying
   metrics are inherently project-specific and cannot be generalized as a fixed
   schema without still reading as one particular kind of project's dashboard.
5. **"the bot" → "the system"**, stack-specific commands → `{{TEST_CMD}}`
   token, a specific project's config-file path → generic "central config
   file, if any", `gh issue view` → cross-referenced to module `25-ticketing`'s
   two variants,
   `analysis/results/` or similar → generic "wherever this project
   keeps generated artifacts", and the writing-style paragraph's specific,
   domain-tailored audience description generalized to "a technically sharp
   reader who is not necessarily a specialist in this project's domain."

### REVIEW (`.claude/skills/AUDIT/SKILL.md` → `REVIEW/SKILL-{lite,full}.md`, both variants)

1. **Gate-evidence rewrite.** Both sentinel-writing CLI invocations (the
   post-fix re-verify write, and the clean-pass write) are rewritten to module
   22's `check_gate_evidence.py --write-evidence <phase>`.
2. **`RISK_PREFIXES` rewrite.** Every hard-coded critical-path prefix list
   (the T1 safety gate, the fix-routing rule, the TODO-debt ceiling, the TODO
   report line) is rewritten to reference this install's `RISK_PREFIXES`
   (module 20) instead of a fixed literal path list.
3. **Domain-example rewrite.** The severity-table's P0/P1 example cells and the
   Tier Re-Classification Check's T3-indicator bullet — all originally
   domain-specific illustrations — are rewritten to domain-neutral
   equivalents: the P0 example now reads "Off-by-one in a core calculation,"
   the P1 impact phrase reads "contained/non-critical impact," and the
   Tier-Reclassification bullet reads "Core business-logic calculations,
   algorithm parameters, calibration/tuning logic."
4. **Seat-routing rewrite (beyond the three named deltas above — required for
   correctness, not cosmetic).** Every hardcoded model-tier reference
   (the finding-generation seat, the fix-escalation seat, the mechanical
   sub-operation seat) is rewritten to the routing profile's seat names
   (Audit reviewer / Workers / Retrieval) — a hardcoded model name would be
   flatly wrong for a Pro-plan install, which gets a different seat assignment
   per `profiles/routing-PRO.md`'s seat table.
5. **The finding-shape's high-stakes flag renamed** (and its justification
   field), matching the RISK_PREFIXES naming scheme rather than assuming a
   financial domain.
6. **`{{SHARED_CODE_HOME}}` ADAPT token.** The hand-mirror/duplication check's
   remediation-target path (a specific shared-code directory in the
   pattern-source project) is replaced with this new ADAPT token — module 26's optional
   ratchet-template component, if installed, targets the same location.
7. **Incident-lore strip.** The duplication-check's incident-class citation,
   the re-verify gate's motivating incident, and the entire
   "Model Routing Provenance" section (a historical footnote about a retired
   validation plan) are removed — none teach a portable lesson without the
   specific history behind them.
8. **ADR-specific bullets dropped, not scrubbed.** Two Step-2b bullets (a
   business-sensitive-figure deny-list grep over ADR docs, and an
   ADR-presence-on-architectural-change check) are removed rather than
   generalized: they enforce a CLAUDE.md rule ("write an ADR for load-bearing
   decisions") that isn't part of any kit module's `claude-md-block.md` — kept
   scrubbed-but-present, they'd check compliance with a policy the kit never
   installs. Their `Override:` escape-valve bullet is dropped for the same
   reason (it existed only to dismiss those two).
9. **PLUS the lite/full split** (Step 10.4/10.5): `SKILL-lite.md` is a
   single-pass review with no round cap, no Step-2b surface diff, no 2b(iii)
   duplication/leanness checks, and no Tier-Reclassification section (this
   profile's tier scope has no T3 to reclassify into). `SKILL-full.md` carries
   the complete round-capped loop, Step 2b/2b(ii)/2b(iii), and Step 4b.
10. **PLUS the 2b(iii)(b) module-26 conditionality** (Step 10.5): the leanness
    baseline-bump guard runs only when `tests/leanness_baseline.json` +
    `tests/test_leanness_ratchet.py` exist in this repo (module 26's optional
    component); it is a documented literal file-presence check, not a
    silently-skipped feature.

### GIT (`.claude/skills/GT/SKILL.md` → `GIT/SKILL-{github,local}.md`, both variants)

1. **Gate-set rewrite.** The single opaque pre-flight "advisor gate" CLI call
   is replaced with the kit's documented, reduced gate set: module 22's
   per-phase evidence check (with the `-RISK` threshold bump computed by this
   skill, not by module 22 — see module 22's own deletion-test note), a
   dossier-file-presence condition for MAP convergence (checked by Read/Glob,
   not a transcript-backed evidence-store mechanism some pattern sources use,
   which is NOT ported), and module 30's playbook-slots check ONLY when that
   module is installed. Override-log path renamed from a pattern-source
   sentinel-store directory to
   `.claude/state/gate-evidence/<branch-slug>/overrides.log`.
2. **`RISK_PREFIXES` rewrite**, matching module 20's tier-suffix naming.
3. **Lint/type step de-scripted.** The source's changed-file-scoped lint gate
   shells out to a project-specific Python script
   (ruff/black/mypy over `src/`+`tests/`) that no kit module ships; the kit
   variant describes the same changed-file-scoped principle using this
   project's own `{{LINT_CMD}}` / `{{TYPE_CMD}}` tokens instead of a
   nonexistent script.
4. **PLUS the github/local split**, selected by interview Q3 — see "GIT-local
   adaptation" below.

## GIT-local adaptation

`GIT/SKILL-local.md` is flagged explicitly as an **adaptation, not a pure scrub**
(per the spec's own callout): the pattern source has no local-only ship path at
all — it only ever ships through a GitHub remote (push → PR → squash-merge).
The local variant keeps the same pre-flight discipline and the same
squash-merge *outcome* (one clean commit on `main`, feature branch deleted) but
reaches it with `git merge --squash <branch>` + `git commit` entirely on the
local machine — no `git push`, no PR, no remote command of any kind. It exists
for members whose project has no GitHub remote in its ship path at all (a solo
local repo, an air-gapped project, or a remote they don't want this kit
touching). Selecting it over the github variant is an interview-Q3 choice, not
a rigor-profile choice — both variants are available at every rigor profile
that installs this module.

## `claude-md-block.md`

See the file itself — the pipeline shape per tier, plus a pointer to the full
delta list and kit tier model in `docs/harness/21-pipeline-skills.md`.
