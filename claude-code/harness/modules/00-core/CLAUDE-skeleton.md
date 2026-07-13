# CLAUDE.md — {{PROJECT_NAME}}

> Auto-loaded by Claude Code every session. This is the lean index — hard rules,
> workflow, and pointers to detail docs. Detail lives in referenced files so this stays
> small as the project grows.

---

## Project overview

<!-- PROJECT-OVERVIEW -->
{{PROJECT_ONE_LINER}} ({{PROJECT_NAME}}).

---

## Hard rules

<!-- HARD-RULES -->
(installed at assembly time: every selected module's `claude-md-block.md`, concatenated
in install order, 00-core's own block first)

---

## Permitted — no confirmation needed

<!-- PERMITTED -->
- Read files, list directories.
- Run tests, lint, and the type-checker in dry-run / read-only mode.
- Create feature branches.

---

## Workflow

<!-- WORKFLOW-TABLE -->
Single-pass, no tiers.

---

## Detail docs

<!-- DETAIL-DOCS-POINTER-TABLE -->
| Doc | When to read | What's in it |
|-----|--------------|--------------|
| `docs/harness/00-core.md` | Before relying on any hard rule above, or on memory/DoD conventions | Full text + rationale for the hard rules, memory conventions, Definition-of-Done shape |

---

## Definition of Done

1. `{{TEST_CMD}}` — zero failures
2. `{{LINT_CMD}}` — clean
3. `{{TYPE_CMD}}` — zero errors
4. Acceptance criteria confirmed with file:line or test name
5. Affected docs updated
