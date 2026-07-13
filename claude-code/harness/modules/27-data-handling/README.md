# Module 27 — data-handling

**Purpose:** reduce PII/client-data mishandling risk when the interview's Q5 ("Will this
project process personal, client, or financial data?") is answered yes. Installs
automatically at ANY resolved rigor profile on Q5 = yes — LIGHT included, since Q5 = yes
also hard-floors the resolution at STANDARD (see `interview/INTERVIEW.md`'s Q5 section),
so in practice this module never actually lands inside a LIGHT-shaped install.

**AC-6 attribution:** kit-authored — pattern source: a common "never expose secrets"
hard-rule pattern, generalized from secrets to PII; no other repo
source, labeled like module `24-skill-delivery`.

**Dependencies:** always co-installed with module `26-code-discipline` via the Q5
STANDARD floor (Q5 = yes removes LIGHT from the resolution and floors at STANDARD;
STANDARD's module set always includes `26-code-discipline`) — this is what makes the
Q5=yes/Q6=no branch of the synthetic-test-data rule non-vacuous (see "Interfaces"
below). Also depends on `10-hooks-base` for the optional WARN hook's shared
`HookResult`/`log_hook_error` helpers — always present alongside this module, since
`10-hooks-base` is itself an unconditional STANDARD+ member.

**Language rule for every sentence in this module's content:** "reduce exposure," never
"guarantee" — checked at validation time (`grep -ic "guarantee"` — every hit must sit in
a negation).

## What ships here

- `files/docs/harness/27-data-handling.md` — the four components in full: deny-list
  CLAUDE.md rules, the synthetic-test-data-only rule and its wiring, Desktop-bound skill
  embedding, and the optional WARN-first PII hook.
- `claude-md-block.md` — short digest naming all four components, "reduce exposure"
  language, installed at every profile that selects this module.
- `settings-fragment.json` — see "Registration" below.
- `files/dot-claude/hooks/lib/pii_pattern_guard.py` — the optional WARN hook itself.
  Kit-authored, stdlib-only.

## Registration — why this module ships its own `settings-fragment.json`

The optional PII hook is a **PreToolUse**-event check, like every dispatcher-routed check
in this kit (module `20-tier-system`'s checks are the reference point) — it runs on the
same per-tool-call event class, follows the same check-function contract
(`check_pii_patterns(stdin_dict) -> HookResult`, imported from `lib/__init__.py`'s
`HookResult`/`log_hook_error`), and never blocks. It is explicitly **not** a standalone
hook in the sense module `23-guards` uses that term — it does not sit on a
session-lifecycle event (Stop/SubagentStop) with a multi-file import closure that
crashes at load if incomplete (`23-guards/README.md`'s "Two standalone hooks" section
describes that failure mode in full). This hook has zero import closure beyond module
10's shared helpers, so it structurally cannot crash from a missing dependency — that is
the sense in which "this one degrades safely if missing."

Because `pii_pattern_guard.py` was not one of the checks anticipated by
`10-hooks-base`'s `pretooluse_dispatcher.py` at the time that file was authored (it has
no pattern-source equivalent — this module is entirely kit-authored, unlike every
`_maybe_register`-guarded check `pretooluse_dispatcher.py` already lists), this module
registers its OWN additional `PreToolUse` entry in its own `settings-fragment.json`
(matcher targeting `Write|Edit|MultiEdit`), rather than depending on an edit to module
10's already-shipped dispatcher file. Claude Code runs every matching `PreToolUse` entry
for a tool call, so this fires alongside — not instead of — module 10's catch-all entry;
the two never conflict, and `pii_pattern_guard.py`'s own logic always returns
`{"decision": "allow"}`.

**Implementation note (labeled — a reviewable design choice, not a silent deviation):**
an alternative design would have added `pii_pattern_guard` to
`pretooluse_dispatcher.py`'s `_maybe_register` list directly, matching module 20's checks
byte-for-byte in mechanism. This module instead ships its own registration to avoid
editing a file outside this module's own payload — the resulting behavior (fires on
every `Write`/`Edit`/`MultiEdit`, fails open, never blocks) is identical either way.

## ADAPT notes

None. The IBAN/card/SSN-shaped regex patterns and the logs/memory-path shape check are
structurally generic — there is no project-specific value for an adopter to fill in.

## Deny-list self-check (Global Constraint 6)

All five files in this module (`README.md`, `claude-md-block.md`,
`files/docs/harness/27-data-handling.md`, `settings-fragment.json`,
`files/dot-claude/hooks/lib/pii_pattern_guard.py`) were checked against the kit's
expanded deny-list — zero hits.

## Interfaces

- The synthetic-test-data-only rule (component 2 in the harness doc) constrains module
  `24-skill-delivery`'s `fixtures/<skill-name>/input.md` contents when that module is
  installed (Q6 = yes), and module `26-code-discipline`'s test-first tests otherwise
  (Q6 = no) — never both for the same deliverable, since a project is either Desktop-bound
  (Q6 = yes) or not.
- The optional WARN hook (component 4) is independent of both of the above — it fires on
  any `Write`/`Edit`/`MultiEdit` whose destination path looks like a logs or memory path,
  regardless of which other modules are installed.
