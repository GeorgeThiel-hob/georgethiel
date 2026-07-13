# Module 25 — ticketing

**Purpose:** ticket-ID conventions plus two variants for where a ticket actually
lives, selected by interview Q3 ("GitHub repo or local-only folder?") — see
`interview/INTERVIEW.md`'s Q3 section. Installs at STANDARD and FULL
(`profiles/rigor-STANDARD.md`, `profiles/rigor-FULL.md`); not offered at LIGHT,
where there is no ticket pipeline for a ticket ID to attach to.

- **github-issues variant** (Q3 = GitHub repo): new tickets are `gh issue create`
  with a ticket ID in the issue title, cross-linked from PM reports (module
  `21-pipeline-skills`'s REPORT variant) by issue number.
- **local `tickets/` folder variant** (Q3 = local-only folder): new tickets are
  files under a bare `tickets/` directory at the adopter's repo root — one file
  per ticket, filename = ticket ID. This directory sits at the repo root, never
  nested under a `docs/` prefix — see "Why the local variant is a bare
  `tickets/`" below for why that distinction matters for this specific kit
  build.

**Ticket-ID non-collision:** before assigning any new ticket ID, enumerate
existing IDs from every authoritative source available in the chosen variant
(commit history always; `gh issue list` for the github variant; the `tickets/`
folder listing for the local variant) and choose one that does not collide. This
module does not restate that check — it is `00-core`'s rule 7
(`files/docs/harness/00-core.md`, "Verify ticket/ID non-collision before naming").
Cross-reference it, don't duplicate it.

**Dependencies:** none. This module ships no hooks and no `lib/` code — it is a
documentation-only module (a harness doc, a CLAUDE.md digest, and — for the local
variant only — a scaffold template), so it does not depend on `10-hooks-base` or
any dispatcher plumbing.

**ADAPT notes:** `{{TICKETING_VARIANT}}` — resolved once, at install time, from
the Q3 answer; every reference to "the ticketing variant" in the installed
CLAUDE.md resolves to whichever of the two this adopter selected. No other
project-specific value.

## What ships here

- `files/docs/harness/25-ticketing.md` — both variants in full: the github-issues
  variant and the local `tickets/` folder variant.
- `files/tickets/README-template-local.md` — the scaffold file, suffixed the same
  way `21-pipeline-skills`' flag-variant skill files are (`-lite` / `-full` /
  `-github` / `-local`), so `START-HERE.md` step 6 applies the identical
  variant-selection discipline: copy it to the destination as
  `tickets/README-template.md` **only** when Q3 resolves to the local variant,
  renaming away the `-local` suffix at copy time. When Q3 resolves to the
  github-issues variant there is no counterpart file to copy — a github install
  gets no `tickets/` folder at all. Unlike module `21-pipeline-skills`'s
  same-destination two-variant selection, this is a single-variant "copy or
  don't" — there is nothing at the destination for this file to collide with, so
  no second, github-suffixed sibling file needs to exist.
- `claude-md-block.md` — the short CLAUDE.md digest every STANDARD/FULL install
  gets.

## Why the local variant is a bare `tickets/`, never nested under a `docs/` prefix

This is one of this kit-build's own constraints (spec §9a / plan Global
Constraint 1), not a general rule the local variant would need in every adopting
project: during authoring, a `docs`-prefixed path with a nested `tickets`
segment would have tripped an internal build-time content guard in the kit's
own authoring environment (a guard that matches a `tickets` path segment
nested anywhere under a `docs` segment). The bare-`tickets/`-at-repo-root
convention is also, independently, a reasonable plain project convention for
an adopter to choose — the two reasons happen to point the same direction,
but only the second one travels with the shipped kit; the first is specific
to how this kit itself was authored.

## Interfaces

- Module `21-pipeline-skills`'s REPORT variant cross-references this module's two
  variants by name when it describes how a ticket gets tracked (github issue
  number, or a file under the local folder).
- The scaffold file (`files/tickets/README-template-local.md`, installed as
  `tickets/README-template.md`) points back to
  `00-core`'s rule 7 for the collision-check procedure rather than restating it —
  keep that pointer, don't duplicate the rule text, if this file is ever edited.
