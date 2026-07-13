# Claude Code Skills

Six Claude Code skills I use in my own build workflow, packaged so each one is a
self-contained folder you can drop into a project. They came out of a larger
workflow harness (see [`../harness/`](../harness/)); these are the reusable,
general-purpose pieces, pulled out and made domain-neutral.

Each skill lives in its own directory with a `SKILL.md` (the file Claude Code's
skill loader reads). To use one, copy its folder into your project's
`.claude/skills/` — and for `COUNCIL`/`DEBATE`, also copy the sibling
`personas.json` (below) into `.claude/skills/`.

## The skills

| Skill | What it's for |
|-------|---------------|
| **GIT** | Ship-it: pushes the current branch, opens a linked PR, merges, and syncs local main. Invoke when tests pass and review is clean. |
| **MAP** | Maps the complete chain of effects of a load-bearing finding or assumption before you build on it — starts at the finding and expands one ring at a time along cause/data-flow edges, adversarially, until nothing new turns up. |
| **REPORT** | Writes a project-state report when a ticket or branch is completed or merged — what changed, key findings, current functionality. |
| **REVIEW** | Severity-gated fix-and-review cycles: when a review or audit finds issues, it loops fix → re-review with bounded rounds until clean. |
| **COUNCIL** | Stochastic multi-agent consensus — spawns N (default 5) parallel analyst agents with distinct personas over the same context, then aggregates mode / divergences / outliers. |
| **DEBATE** | Spawns 5+ agents into a shared room to debate, disagree, and converge, using round-robin turns with parallel execution within each round. |

## How to use a skill

1. Copy the skill's folder (e.g. `MAP/`) into your project's `.claude/skills/`.
2. For `COUNCIL` and `DEBATE`, also copy `personas.json` into `.claude/skills/`
   (it must sit as a sibling of the skill folders, at `.claude/skills/personas.json`).
3. Restart Claude Code in that project so the skill loads.

## Standalone vs. full harness

These skills were cut from a workflow harness, so some of what they reference is
harness machinery. Here's the honest dependency line.

**Sibling-required, but fully functional standalone — `personas.json`.**
`COUNCIL` and `DEBATE` read their persona roster from
`.claude/skills/personas.json` (COUNCIL resolves it at `SKILL.md` pre-flight;
DEBATE loads it at runtime through `debate.py`). It ships here as a sibling of the
skill folders, so as long as you copy it alongside the skill, **COUNCIL and DEBATE
work standalone** — no harness install needed.

**Harness-required, but degrades gracefully standalone.** Several references only
resolve after a full harness install (see [`../harness/`](../harness/)):

- The `{{TEST_CMD}}` / `{{LINT_CMD}}` / `{{TYPE_CMD}}` template tokens in `GIT`,
  `REVIEW`, and `REPORT` — the harness installer fills these in per-project; bare,
  they stay literal.
- Hook shell-outs — `check_gate_evidence.py` (GIT, MAP, REVIEW) and
  `schema_validator.py` (COUNCIL, and `DEBATE/debate.py`). These live in the
  harness, not in a skill folder.
- `profiles/routing-*.md`, `RISK_PREFIXES`, and module-number cross-references
  (e.g. `20-tier-system`), plus a few doc cross-refs.

Without the harness, these skills still read as complete process playbooks — you
lose the automated hooks and the pre-filled commands, not the method. `DEBATE`
degrades cleanly: if `schema_validator.py` is absent, `debate.py`'s delta
validation just returns `False` rather than crashing (`debate.py` handles the
missing import). For the whole apparatus wired together, install the harness.

## Variants

Two skills ship a primary `SKILL.md` plus an alternate you can swap in by renaming:

- **GIT** — `SKILL.md` is the GitHub/PR flow. `SKILL-local.md` is the alternate for
  non-GitHub / local-only flows (rename it to `SKILL.md` to use it instead).
- **REVIEW** — `SKILL.md` is the full severity-gated loop. `SKILL-lite.md` is a
  lighter single-pass review (rename it to `SKILL.md` to use it instead).

## A note on one dangling reference

`REPORT/SKILL.md` mentions an `excluded/README.md` "write-your-own-gate" example
that isn't published in this repo (it was omitted from the harness copy). Treat
that as an illustrative pointer, not a file to look for.
