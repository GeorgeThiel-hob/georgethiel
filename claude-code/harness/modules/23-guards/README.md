# Module 23 — guards

**Purpose:** the WARN-first guard pack — the citation guard, the claim-binding
guard, the circularity guard, and the confidence-label scan — plus the full
verified import closure those four checks need to load. FULL-profile-only
(see `profiles/rigor-FULL.md`); not installed at STANDARD.

**Dependencies: `10-hooks-base` (hard).** This module's three `lib/` guard
files (`claim_binding_guard.py`, `circularity_guard.py`, `reexec_guard.py`)
import `HookResult` / `log_hook_error` from `lib/__init__.py:8,13` — module
10's file, not this module's. The installer's module-dependency validation
(spec §5) must reject an override that selects this module while dropping
module 10. This is the one module in the whole kit where two hooks are **NOT**
dispatcher-routed (see "Two standalone hooks" below), so module 10's
`_maybe_register` import-guard does not protect a missing dependency here —
it crashes the hook at load instead of degrading gracefully.

**ADAPT notes:** none. Every check in this module is structurally generic —
there is no project-specific value for an adopter to fill in.

## What ships here

- `files/dot-claude/hooks/stop_citation_guard.py` — the Stop hook. **BLOCK-grade**
  (see `docs/harness/23-guards.md`'s WARN-first-before-BLOCK section for why
  this one check is the exception).
- `files/dot-claude/hooks/subagentstop_log.py` — the SubagentStop hook. Logs
  subagent failures (best-effort) and runs the confidence-label scan
  (`maybe_log_label_misses`) — log-only, non-blocking.
- `files/dot-claude/hooks/lib/claim_detector.py` — shared claim-detection
  primitives (`Finding`, `scan_for_uncited_claims`, `scan_for_quantifier_claims`,
  `scan_for_unlabeled_claims`). Imported by both hooks above. stdlib-only
  (`re`, `dataclasses`).
- `files/dot-claude/hooks/lib/transcript_utils.py` — transcript-reading
  helpers (`load_entries`, `advisor_calls`, `has_advisor_call`). Imported by
  `stop_citation_guard.py`. stdlib-only (`json`, `collections`).
- `files/dot-claude/hooks/lib/claim_binding_guard.py` — WARN-grade
  directive-forcing gate (`check_claim_binding`). Kit variant — see
  "Kit-variant deltas" below.
- `files/dot-claude/hooks/lib/circularity_guard.py` — WARN-grade
  circularity-rejection gate (`check_circular_evidence`). Kit variant — see
  "Kit-variant deltas" below.
- `files/dot-claude/hooks/lib/reexec_guard.py` — the recompute-and-compare
  PreToolUse guard (`check_reexec_directives`) the two WARN guards above both
  depend on for fence-aware directive parsing. Kit variant — see
  "Kit-variant deltas" below.
- `files/dot-claude/hooks/lib/post_edit.py` — **kit-authored, NEW.** Extracts
  the single generic `_post_edit_content(file_path, tool_name, tool_input) -> str`
  helper out of a pattern-source PM-report linter module (excluded from
  this kit — its other logic is a project-specific numeric-denominator
  gate, out of scope here). stdlib-only (`pathlib`); imported by all three
  guard files above.
- `files/docs/harness/23-guards.md` — the WARN-first-before-BLOCK rationale in
  full, the import-closure map as a table, and a concrete fenced `reexec:`
  directive example.
- `claude-md-block.md` — the short CLAUDE.md digest every FULL-profile install
  gets.
- `settings-fragment.json` — registers this module's two standalone events
  (`Stop` → `stop_citation_guard.py`, `SubagentStop` → `subagentstop_log.py`).

## Two standalone hooks — not dispatcher-routed

`stop_citation_guard.py` (Stop) and `subagentstop_log.py` (SubagentStop)
register via **this module's own** `settings-fragment.json`, not via
`pretooluse_dispatcher.py`'s `dispatch()`. That means module 10's
import-guarded `_maybe_register` mechanism — which lets an absent optional
module's checks simply not register instead of crashing the dispatcher — does
**not** cover them. Their full dependency closure (the 2 hook files, the 5
`lib/` files above, and module 10's `lib/__init__.py`) MUST all be present, or
these two hooks crash at load instead of degrading gracefully. This is the
one place in the whole kit where a missing dependency is a hard failure, not
a guarded no-op — see `docs/harness/23-guards.md` for the full closure table.

## Kit-variant deltas (AC-6)

**AC-6 delta name:** "the module-23 import rewrite (`.pm_report_checks` →
`.post_edit` at `claim_binding_guard.py:32`, `circularity_guard.py:23`,
`reexec_guard.py:31`)" — shipped verbatim, these three files would `ImportError`
on the excluded `pm_report_checks` module and the guards would go vacuous.
Applied to all three `lib/claim_binding_guard.py`, `lib/circularity_guard.py`,
`lib/reexec_guard.py` files; no other line in any of the three differs from
source apart from the two deltas below.

**Second delta — dossier-filename rename → `map-dossier.md`.** The source
dossier artifact's original filename is itself one of this kit's deny-listed
literal tokens (module 21's MAP variant already renamed it kit-wide, per
`21-pipeline-skills/README.md`'s own "Dossier-filename rename" delta — see
that file for the literal string; it is not repeated here). This module's
guards must watch for the SAME filename MAP actually writes, or
`circularity_guard.py`'s file-targeting check (`rel.name == _DOSSIER_BASENAME`)
would silently never fire on any kit install. Renamed: `circularity_guard.py`'s
`_DOSSIER_BASENAME` constant (source line 35) plus its two docstring/comment
mentions (source lines 5, 76), and `claim_binding_guard.py`'s one docstring
dossier-path mention (source line 16, also generalizing the source's
dated, ticket-ID-shaped example slug to `<investigation-slug>`, consistent
with module 21's directory-convention note). Zero logic change —
`_is_dossier_citation`'s bounded-segment matching and the file-targeting check
both key off the constant, so the rename is a one-line source-of-truth edit
per file, not a scattered find/replace.

**Third delta — deny-list + incident-lore scrub (AC-11).** Two classes of
fix (a later Opus audit round additionally neutralized one *functional* regex —
see the audit-neutralization note after this list). Both classes below are
comment/docstring-only, with zero behavioral change to any function body or
regex:

1. A literal deny-list hit survived in an otherwise-generic illustrative
   comment: `claim_detector.py` (source line 79)'s file:line example used a
   project-specific module name as its illustration; the comment's example
   filename was swapped for the domain-neutral `model_fit.py:123` (that swap left
   the regex itself, `CITATION_PATTERN`, unchanged; its unit set was later
   neutralized in the Opus audit round — see the audit-neutralization note below).
2. AC-11(b)'s fresh-context-reviewer standard (no repo-specific proper nouns
   or incident lore survive) required stripping, across all seven `.py`
   files in this module, several classes of source-project-specific
   provenance markers that don't affect behavior: calendar-date annotations
   on tuning comments (generalized to "owner decision" / "tuning note" /
   "found via review"), this project's ticket-ID prefix convention as it
   appeared in docstring headers (dropped — the plain descriptive sentence
   that followed each one already stands on its own), a bare epic-numbering
   shorthand (dropped for the same reason), concrete transcript
   session-hash/entry-index examples from one specific past debugging
   session (generalized to "verified in-env" — the behavioral claim they
   supported is unchanged, only the illustrative example numbers are gone),
   a specific past investigation's internal node-reference codes (replaced
   with the plain descriptive prose that follows each code in source), an
   internal tuning-corpus label (generalized to "tuning corpus"), a
   rule-number citation (dropped — the sentence stands without it), and one
   specific incident's dollar figure (generalized to "a real incident where a
   fabricated claim compounded through a chain of prior dossiers"). Every
   one of these seven files is otherwise structurally and behaviorally
   identical to its source, with the single exception recorded next.

**Fourth delta — Opus audit-round neutralization.** The final Opus verifier
found domain-specific illustrative values surviving in `claim_detector.py`'s
regex comments, and a *functional* leak: `CITATION_PATTERN`'s number-plus-unit
alternation hard-coded a set of source-domain-specific units. Both were
neutralized — the comments to domain-neutral examples, and the unit set to a
generic `%|ms|kb|x`. This is a deliberate **behavioral** change to
`CITATION_PATTERN` (different number+unit strings now register as citation
tokens) — the one regex in this module that diverges from source.

`post_edit.py` has no delta to report — it is a NEW kit-authored file (its
docstring says so), not a modified copy of anything.

## Genericity note

`claim_detector` (`re`/`dataclasses`), `transcript_utils` (`json`/`collections`),
and the extracted `post_edit` module are stdlib-only. `reexec_guard` is
**NOT** — it imports `lib/__init__` (module 10) and this module's own
`post_edit`.

## Interfaces

- `stop_citation_guard.py` imports `lib.claim_detector` (`Finding`,
  `scan_for_quantifier_claims`, `scan_for_uncited_claims`) and
  `lib.transcript_utils` (`load_entries`).
- `subagentstop_log.py` imports `lib.claim_detector` (`scan_for_unlabeled_claims`).
- `lib/claim_binding_guard.py` imports `lib/__init__` (`HookResult`),
  `.claim_detector` (`CITATION_PATTERN`), `.post_edit` (`_post_edit_content`),
  and `.reexec_guard` (`_fenced_line_flags`, `_iter_directives`).
- `lib/circularity_guard.py` imports `lib/__init__` (`HookResult`,
  `log_hook_error`) and `.post_edit` (`_post_edit_content`).
- `lib/reexec_guard.py` imports `lib/__init__` (`HookResult`,
  `log_hook_error`) and `.post_edit` (`_post_edit_content`).
- No file in this module is a caller of anything in another kit module except
  the `lib/__init__.py` dependency on module 10 documented above.
