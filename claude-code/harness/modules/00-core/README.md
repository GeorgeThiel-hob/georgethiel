# Module 00-core

## Purpose

The dependency root of every rigor profile. `00-core` ships the CLAUDE.md skeleton
every other module's `claude-md-block.md` fragment merges into, plus its own hard-rule
block: the universal engineering discipline this kit assumes at every rigor tier —
never-assume-with-confidence-labels, systematic-debugging for bugs, a deterministic
feedback loop before hypothesising, environment-verified "fixed" claims, verify-before-
complete, a lessons log, and ticket-ID collision checks — plus the memory-conventions
paragraph and the Definition-of-Done shape every profile installs.

This module owns the skeleton's slot structure (`CLAUDE-skeleton.md`, module-level —
sitting beside this `README.md`, not under `files/`, because it is an assembly input
step 6 consumes to *produce* the destination `CLAUDE.md`, never a payload file copied
as-is): the `<!-- PROJECT-OVERVIEW -->`, `<!-- HARD-RULES -->`, `<!-- PERMITTED -->`,
`<!-- WORKFLOW-TABLE -->`, and `<!-- DETAIL-DOCS-POINTER-TABLE -->` markers. Every other
module's `claude-md-block.md` is inserted into these slots at install time
(`START-HERE.md` §3(a), fresh-repo case) — a later module must not invent its own
CLAUDE.md structure; it fills these slots.

`00-core` ships a second assembly input the same way: `gitignore-block.md`
(module-level, beside this `README.md`, not under `files/`). Its content, verbatim, is
what step 6 places between the `# BEGIN handoff-kit harness` / `# END handoff-kit
harness` markers in the destination `.gitignore` — see `START-HERE.md` §3(e) for the
fresh-vs-merged assembly rule. Like `CLAUDE-skeleton.md`, it is never deposited at the
destination as a stray `gitignore-block.md` file.

## Dependencies

None. `00-core` installs at every rigor profile (LIGHT, STANDARD, FULL) and is the base
every other module depends on, directly or transitively.

## ADAPT notes

- `{{PROJECT_NAME}}` and `{{PROJECT_ONE_LINER}}` — substituted into the skeleton's
  `<!-- PROJECT-OVERVIEW -->` slot. No interview question binds these directly; use the
  member's own project description from the install conversation.
- `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPE_CMD}}` — substituted into the Definition-of-Done
  section of the skeleton, bound from interview Q7 ("What's your stack?"). If the member
  answered "no code," bind all three to the literal string `N/A` (per
  `interview/INTERVIEW.md` Q7's pinned reading), rather than leaving template tokens
  unresolved.

## Provenance (AC-6)

Kit-authored, modeled on a pattern-source CLAUDE.md's lean-index design (spec §9 00-core
row) — not a verbatim copy of that CLAUDE.md (which is itself
project-specific); the universal subset of its hard rules is extracted and scrubbed.
