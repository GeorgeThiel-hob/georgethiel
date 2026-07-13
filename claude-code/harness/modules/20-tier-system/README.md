# Module 20 — tier-system

**Purpose:** T1/T2/T3 tier classification, plus the standing-brief and
plan-by-reference discipline that gates execute-phase subagent dispatches. A
`-RISK` suffix (this module's divergence check) auto-promotes a ticket's declared
tier when the real diff touches a path the adopter has named as "touches
something hard to undo" — schema, payments, auth, production config, whatever
that means for their project.

**Dependencies:** `10-hooks-base` (this module's checks are dispatcher-routed —
called from inside `pretooluse_dispatcher.py`'s `dispatch()`, not registered via
their own `settings-fragment.json` event). This module ships no
`settings-fragment.json` of its own.

## What ships here

- `files/dot-claude/hooks/lib/tier_detection.py` — **kit variant** of
  `.claude/hooks/lib/tier_detection.py`. See "Kit-variant deltas" below.
- `files/dot-claude/hooks/lib/task_checks.py` — **kit variant / subset** of
  `.claude/hooks/lib/task_checks.py`. See "Kit-variant deltas" below.
- `files/dot-claude/hooks/lib/brief_paths.py` — **verbatim copy** of
  `.claude/hooks/lib/brief_paths.py`. Byte-identical; not a spec-named file, but
  a required transitive dependency — see "Spec-gap fix" below.
- `files/docs/harness/20-tier-system.md` — the LITE (STANDARD-profile) and FULL
  (FULL-profile) tier tables.
- `claude-md-block.md` — the CLAUDE.md rule-block fragment installed at every
  profile that selects this module.

## Kit-variant deltas (AC-6)

**AC-6 delta names:** "RISK_PREFIXES generalization (renamed from the pattern
source's equivalent risk-path constant)" and "tier-divergence block message
drops the live-state-probe instruction."

### `tier_detection.py`

Three mechanical renames from source, plus one content deviation:

1. The module-level risk-path tuple (source uses a differently-named constant
   of the identical shape — that name is itself on this kit's AC-11 deny-list,
   so it is not repeated here) → `RISK_PREFIXES`.
2. Every constructed `"-LIVE"` tier suffix (in `detect_tier_promotion` /
   `effective_tier`) → `"-RISK"`.
3. `any_live_path` → `any_risk_path` (logic unchanged).

**Content deviation (not a rename — required to stay deny-list clean):** the
source tuple ships nine project-specific path strings — source-code directory
prefixes and config/entry-point filenames specific to the pattern-source
project. Several of those nine literal strings are separately named,
individually, on this kit's AC-11 deny-list, and the remaining ones are equally
repo-specific — so the tuple body ships as an **empty tuple**
(`RISK_PREFIXES: tuple[str, ...] = ()`) rather than a byte-identical copy of the
source values. This is the ADAPT note below, applied at the value level rather
than left as a `{{TOKEN}}` placeholder (a Python tuple literal can't hold an
unresolved template token and stay `ast.parse`-valid). Everything else in the
file — including bare, non-renamed occurrences of the word "LIVE" left in
docstring prose by the three mechanical renames above (e.g. "when a LIVE path
matches") — is untouched, matching source exactly modulo the three renames.

**ADAPT note:** `{{RISK_PREFIXES}}` — the adopter's list of "touches something
hard to undo" path prefixes, to be filled in post-install. `()` (the shipped
default) is legal and correct for a project with no such paths — the divergence
check is simply inert until the adopter opts in with their own list.

### `task_checks.py`

Extracted ONLY `_resolve_line_range_refs`, `check_plan_by_reference`,
`require_standing_brief`, `_check_tier_divergence` — the spec's named scope
(standing brief + plan-by-reference + the divergence-check pattern). Dropped
`_extract_acceptance_criteria_block`, `check_ac_id_prefix`,
`block_finishing_branch_skill` (and their now-unused regex constants) — not
named in this module's spec row, out of scope for this kit as specified.

**`require_standing_brief` is deliberately KEPT in this subset**, not dropped.
The STANDARD-profile brief experience (a one-line brief, not the full Rule-8
shape) is handled by documentation — see `claude-md-block.md` and
`files/docs/harness/20-tier-system.md` — not by omitting the enforcing function.
Every profile that installs this module gets the same gate; only the expected
brief content differs by profile.

Renamed every reference to the source risk-path constant (see the note above —
same constant `tier_detection.py` renames) to `RISK_PREFIXES`, and every `-LIVE`
tier-suffix literal to `-RISK`, matching `tier_detection.py`'s renames.

**Block-message scrub:** `_check_tier_divergence`'s block message originally
read "...and re-run the live-state probe before continuing." This kit ships no
live-state-probe concept (that is a pattern-source-specific pre-flight
mechanism, not a generic kit feature), so the clause is rewritten to "...and
re-verify the tier scope before continuing."

### Cross-task note — the dropped functions are load-bearing for module 10, not a gap

Module 10's `pretooluse_dispatcher.py` (`_maybe_register`) registers
`check_ac_id_prefix` and `block_finishing_branch_skill` from `task_checks` behind
a `try/except (ImportError, AttributeError): pass` guard specifically so that
this module's subset — which drops both — degrades safely instead of crashing
the dispatcher. Do not re-add either function here to "avoid" the
`AttributeError`; the guard is the intended mechanism, and re-adding them would
reintroduce scope this module's spec row does not name.

## Spec-gap fix — `brief_paths.py`

`task_checks.py` imports `.brief_paths` for `resolve_brief_path`, used by
`require_standing_brief`. This is a transitive dependency the module-20 spec row
does not name explicitly; without shipping it, every STANDARD/FULL install's
import-closure self-check would fail. `brief_paths.py` is 23 lines, fully
generic (resolves a branch slug to a brief path under
`docs/superpowers/briefs/`), and ships byte-identical to source.

## `claude-md-block.md`

See the file itself — short digest of the tier ladder plus the one-line
standing-brief instruction (NEW-2-KIT: STANDARD documents the one-line brief
rather than omitting the gate).

## Interfaces

Module 21's skill variants reference this module's tier tables and the
`RISK_PREFIXES` divergence check (e.g. the REVIEW variant's severity table, the
GIT variant's tier check).
