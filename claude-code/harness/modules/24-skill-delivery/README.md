# Module 24 — skill-delivery

**Purpose:** a fixture-testing loop plus a Desktop self-containment check, for any
skill whose deliverable will be consumed by people on the Claude Desktop app rather
than driven from inside this harness. Binds when interview Q6 ("Will deliverables
be used by people on the Claude desktop app?") is answered yes — see
`interview/INTERVIEW.md`'s Q6 section. Installs at **any** resolved rigor profile,
LIGHT included (`profiles/rigor-LIGHT.md`): a Desktop-bound skill needs this check
regardless of how much process weight the rest of the deliverable carries.

**Provenance (AC-6):** authored fresh — NO proven source in the pattern-source project. This module
has no verbatim or scrubbed-variant origin file the way every other numbered module
does — it is new content, written for this kit, in the same honesty class as module
`26-code-discipline`'s lean-code slice (also authored fresh, also labeled as such in
its own README).

**Dependencies:** none. This module ships no hooks and no `lib/` code — it is a
documentation-only module (a harness doc + a CLAUDE.md digest), so it does not
depend on `10-hooks-base` or any dispatcher plumbing the way the hook-bearing
modules do.

**ADAPT notes:** none. Every rule in this module is structurally generic — there is
no project-specific value for an adopter to fill in.

## What ships here

- `files/docs/harness/24-skill-delivery.md` — the fixture-testing loop in full,
  plus the Desktop self-containment checklist.
- `claude-md-block.md` — the short CLAUDE.md digest every install that binds this
  module (any profile, Q6 = yes) gets.

## Scope note (load-bearing — appears verbatim in the harness doc too)

The check applies to the DELIVERED artifact, not the build harness — the skill
being shipped may only use what Desktop offers (uploads, conversation, artifacts —
no repo tools, hooks, subagents), while the FULL/STANDARD harness building it uses
everything it has.

Concretely: while you are *building* a skill for Desktop delivery, your Claude Code
session has the full harness available — repo file access, hooks, subagents,
whatever this install selected. None of that travels with the finished skill. The
skill's own instructions are what a Desktop user's session actually runs, and that
session offers only file uploads, the conversation itself, and artifacts. A skill
whose instructions say "check the file at `docs/...`" or "dispatch a subagent to
verify this" will fail silently or confusingly for a Desktop user, because neither
capability exists there. The self-containment checklist below exists to catch that
class of mistake before delivery, not to restrict how the skill gets built.

## Interfaces

- **Fixture-pair convention** (defined in full in `files/docs/harness/24-skill-delivery.md`):
  a fixture for skill `<skill-name>` is the pair `fixtures/<skill-name>/input.md` +
  `fixtures/<skill-name>/expected-output.md`. Any other module that needs to attach
  a constraint to "the sample input a Desktop skill is tested against" (for example
  a data-handling module requiring that sample input be synthetic, never real
  client data) hooks in by constraining the *contents* of `fixtures/<skill-name>/input.md`
  — it does not change the mechanism (build → run against input → diff against
  expected-output → iterate until it matches).
- Module `26-code-discipline`'s test-first requirement is the non-Desktop
  equivalent of this module's fixture loop — a project with Q6 = no gets test-first
  TDD instead of fixture testing, never both for the same deliverable.
