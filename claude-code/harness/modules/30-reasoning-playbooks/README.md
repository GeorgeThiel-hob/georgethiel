# Module 30 — reasoning-playbooks

**Purpose:** opt-in reasoning playbooks (bug-investigation, data-analysis, ticket-scoping) +
the escalation ladder + the ship-time slots WARN check + the pre-registration template. Each
playbook targets one recurring session shape and defines mandatory evidence-shaped
checkpoints ("slots") for that shape, so a session's missing thought is visible instead of
silently absent.

**Offered on Max 5x / Max 20x plans only** (interview Q8, gated by Q2's plan tier) — a
session shape this deep in per-session reasoning overhead assumes a usage budget PRO does not
have.

## Dependencies

- **`22-second-opinion-seat` (required).** The escalation ladder's degradation rule
  ("strongest-seat → strongest available, never self-review") is a direct application of that
  module's seat abstraction — the ladder routes TO the second-opinion seat, it does not define
  its own.

ADAPT note: no `{{...}}` template tokens are used by this module — see the
`playbook_slots.py` ADAPT note below instead, which is a path-convention retarget (named
Python constants), not a template substitution.

## What ships here

- `files/docs/orchestrator-playbooks/README.md` — scrubbed variant: the "which playbook"
  index + the escalation ladder + the degradation rule.
- `files/docs/orchestrator-playbooks/bug-investigation.md` — scrubbed variant.
- `files/docs/orchestrator-playbooks/data-analysis.md` — scrubbed variant.
- `files/docs/orchestrator-playbooks/ticket-scoping.md` — scrubbed variant.
- `files/docs/orchestrator-playbooks/pre-registration-template.md` — scrubbed variant (no
  named residue found on a full read; the deny-list self-check is the operative
  scrub-completeness signal for this one file).
- `files/dot-claude/hooks/lib/playbook_slots.py` — kit variant: WARN-first, fail-open,
  ship-time slot-presence check. See its own module docstring + the delta row below.
- `claude-md-block.md` — the compact CLAUDE.md digest for any profile installing this module.

None of these are verbatim copies (copy-only invariant, satisfied by authoring the variant
once, here, at cut time — the installer still only copies).

`strategy-audit.md` is **NOT ported** — its absence from
`files/docs/orchestrator-playbooks/` is itself the required state. The source project used
that fourth playbook to gate changes to its own core strategy/execution logic; that is a
domain-specific gate, not a portable one. `excluded/README.md` carries it as the
write-your-own-domain-gate example.

## Delta list (AC-6 / AC-9 — every delta named, not just "scrubbed")

| File | Source (this build's source repo) | Delta |
|---|---|---|
| `README.md` | `docs/orchestrator-playbooks/README.md` | Provenance-authorship self-ID line (model codename, date, session id) dropped as pure incident lore. The metric-example phrase naming this project's three headline domain-specific metrics (source line 91) replaced with "accuracy, cost, or calibration metrics" (Step 15.2's own suggested wording). Every reference to the source project's internal escalation-seat name is generalized to "strongest-seat" throughout. The experimental per-prompt digest paragraph (citing a project-specific `UserPromptSubmit` hook module not shipped by any kit module) dropped — the primary once-per-shape read channel is kept, the unsettled secondary channel is not. Every dated incident citation (a specific date + burn-percentage, a specific ticket ID, a named incident-history doc + line numbers, a specific out-of-scope skill's review event) generalized to describe the failure MODE without the date/ID/doc citation — that skill is out of scope for this kit (spec §10) so its citation is dropped, not scrubbed-in-place. Internal CLAUDE.md rule numbers generalized to plain descriptions. The fourth-shape playbook row dropped from the "which playbook" table and its ladder seat-batching example clause removed (not ported — see "What ships here" above); a one-line pointer to `excluded/README.md` added in its place. |
| `bug-investigation.md` | `docs/orchestrator-playbooks/bug-investigation.md` | Every parenthetical citation of the source project's own mistake-log line numbers (6 occurrences) rewritten to state the failure pattern it illustrates without the log-line citation or specific incident name (e.g. a fail-open-but-silently-inert incident, a lock-mechanism over-generalization, a stale-file near-miss). The dated, percentage-quantified motivating incident in `SLOT:repro-loop` generalized to "most of a session burned chasing the wrong root cause". The Phase-B header's incident-count citation (a specific doc + two line ranges) generalized to "consistently the single largest failure class in past investigations". Every reference to the source project's internal escalation-seat name generalized to "strongest-seat". "CLAUDE.md ... rule" phrasing generalized to "a standing project rule". |
| `data-analysis.md` | `docs/orchestrator-playbooks/data-analysis.md` | The domain-metric-bearing examples named in spec §9 replaced with domain-neutral equivalents: the title drops the two named domain-specific metric abbreviations → "Data / Metric / Calibration Analysis"; `SLOT:population`'s named row-count/percentage example and its two project-specific column/table-literal citations replaced with a domain-neutral "cut a dataset by an order of magnitude and inverted the published result" statement plus a generic synthetic/seed-row exclusion instruction; `SLOT:regime-segmentation`'s two named-incident citations replaced with a domain-neutral lumping-vs-segmenting statement; `SLOT:unit-audit`'s named unit-pair / column-naming citation replaced with a domain-neutral mixed-unit-column statement; `SLOT:framings`'s a named domain-specific example replaced with a domain-neutral selection-artifact statement. `SLOT:confidence-table`'s named statistics-helper-function citation replaced with "a Wilson interval or equivalent for any proportion/rate metric". Every reference to the source project's internal escalation-seat name generalized to "strongest-seat". Doc-path pointer to two project-specific doc sections genericized to "your project's analysis-mistakes log and domain glossary, if maintained". |
| `ticket-scoping.md` | `docs/orchestrator-playbooks/ticket-scoping.md` | The domain-specific-term reference named in spec §9 ("lifetime live count = 0" for a specific production mechanism) replaced with "a lifetime production execution count of zero", with the specific ticket numbers and an internal rule-numbering citation dropped. Every remaining parenthetical citation of the source project's own mistake-log or durable-memory filenames (4 occurrences) rewritten to state the pattern without the citation. "gh issues" genericized to "issue tracker". The project-specific scope-ledger filename and durable-memory doc name genericized to "your durable memory/decisions log" / "any in-flight epic/roadmap scope file your project keeps". Every reference to the source project's internal escalation-seat name generalized to "strongest-seat". |
| `playbook_slots.py` | `.claude/hooks/lib/playbook_slots.py` | See the ADAPT-ergonomics note below (Step 15.8) for the constant-extraction refactor. Separately, as a scrub (not an ergonomics change): the dossier basename is renamed to `map-dossier.md` (matching this kit's `21-pipeline-skills` MAP variant, which ships the same renamed dossier filename — the two must agree or the WARN check's exclusion silently stops matching; the pre-rename basename is itself one of this kit's deny-listed literals, so it is not cited here — see module 21's own README for the same convention). The third shape-detection key (keyed on this kit's deny-listed execution/strategy/calibration path-prefix literals plus a settings-file glob) is dropped entirely, not parameterized: since the fourth playbook is not ported (Step 15.7), a shape whose WARN message points at a non-shipped playbook file would be broken-by-design, not merely domain-specific. The module docstring's citations of a specific ticket ID, a specific ADR number, and the source project's sentinel-writing CLI module name are removed; the last is replaced with a reference to this kit's `21-pipeline-skills` module's GIT skill `--check` gate step, the actual ship-time caller that supplies branch/added_files/changed_paths/brief text. |

## `playbook_slots.py` ADAPT-ergonomics note (Step 15.8 — not one of the deltas above)

The kit variant extracts the three hardcoded path-convention strings into named
module-level constants (`_TICKETS_DIR`, `_ANALYSES_DIR`, `_MAP_DOSSIER_NAME`) at the top of
the file, immediately below the shape-name constants, so an adopter who uses different
directory conventions retargets all three in ONE place instead of hunting through function
bodies. This is a light refactor-FOR-adaptability, not a functional change — the detection
logic is byte-identical in behavior to the pre-refactor version for the default values. It
is called out here separately from the delta table above because it is not a scrub of
project-specific content; it is an ergonomics improvement over the source project's own
version of this file, which never needed the constants extracted (a single-repo deployment
has no "adopter" to retarget for).

## Confirmed: the fourth playbook is not ported (Step 15.7 / AC-9)

Its absence from `files/docs/orchestrator-playbooks/` is itself the required state. See "What
ships here" above and `excluded/README.md`'s write-your-own-domain-gate example.

## `claude-md-block.md`

See the file itself — a short digest of the playbook set + the escalation ladder's
degradation rule, pointing to `docs/orchestrator-playbooks/README.md` as the detail doc (the
playbooks themselves ARE the detail doc for this module — no separate `docs/harness/` file is
needed).
