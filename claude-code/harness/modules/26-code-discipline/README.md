# Module 26 — code-discipline

**Purpose:** the "lean, simple, robust, readable" axis of the harness — a kit-authored
composition of coding-standard prose plus one optional mechanical backstop. Installs at
STANDARD and FULL (see `profiles/rigor-STANDARD.md`, `profiles/rigor-FULL.md`); not part of
LIGHT's module set.

**Dependencies:** none required for the three prose slices below. The optional
leanness-ratchet test template ships INACTIVE, as `files/tests/test_leanness_ratchet.py.template` +
`files/tests/leanness_baseline.json.template` — the `.template` suffix keeps pytest from
collecting the test on a fresh install (a `.py.template` file is not a test module). It has
no additional dependency of its own beyond a Python project with `pytest`, a pinned `ruff` in
`requirements.txt`, and source code under some scan root (default `src/`, ADAPT note below).
Opting in (renaming the templates back to live `.py`/`.json` and generating the adopter's own
baseline) is a manual, per-adopter step — see `files/tests/README.md` for the exact commands.
Once active, it is read by module `21-pipeline-skills`'s REVIEW-full Step 2b(iii)(b), but does
not itself depend on module 21 being installed — it runs standalone via `pytest` either way.

## Per-slice attribution (AC-12 — three named slices + the test-first policy, each
independently labeled, not blended into one paragraph)

1. **Slice 1 — code-conventions generic subset.** Sourced from a pattern-source
   code-conventions document: its Naming, Logging, Error Handling, SQL Safety, and
   Tagged-debug-logs rules — **MINUS** that document's domain-bound sections (a
   financial-precision/dollar-rounding rule, and a specific async/sync
   client-bridging pattern tied to one third-party SDK), and minus a
   project-specific data-field-naming convention section. One
   Logging line naming two project-specific source directories was also dropped as
   project-bound, not because the section it lived in was excluded.
2. **Slice 2 — lean-code principles.** Provenance label: **kit-authored, NO direct pattern
   source** (grep-verified 2026-07-06: no prior document states these
   principles as such — they are standard software practice, labeled newly-authored
   exactly like module `24-skill-delivery`'s fixture-testing loop) — small functions, no
   speculative abstraction, comment discipline.
3. **Slice 3 — architecture-vocabulary.** Sourced from a pattern-source
   architecture-vocabulary reference, near-fully generic — the deletion test on every new
   module, divergent interface shapes before elaborating one, depth over surface. Only the
   project-specific illustrative file:line examples were scrubbed (replaced with an
   invented, domain-neutral example); the term definitions and the deletion test itself are
   unchanged.
4. **Test-first policy.** Labeled explicitly as **a kit policy choice, not a straight
   port** — the installed CLAUDE.md mandates invoking
   `superpowers:test-driven-development` (a Superpowers-plugin prerequisite) for code work,
   whereas the pattern source's own rule is tests-*required*, not test-*first*. Say so
   plainly in the installed CLAUDE.md digest — don't let the stricter kit default read as
   if it were always the pattern source's rule.

## What ships here

- `files/docs/harness/26-code-discipline.md` — the full text of all three slices plus the
  test-first policy statement, in one detail doc.
- `claude-md-block.md` — short digest naming all four elements, per AC-12's "the installed
  CLAUDE.md template references all of them."
- `files/tests/test_leanness_ratchet.py.template` — **optional, opt-in component**,
  generalized from a pattern-source project's own `tests/test_leanness_ratchet.py`. Ships
  unmodified apart from the ADAPT note below and the `.template` suffix (see `files/tests/README.md`
  for why and how to activate) — the scanner's own default scan-root list (`["src/"]`) was
  already generic in source, not a project-specific literal, so no code edit was needed there.
- `files/tests/leanness_baseline.json.template` — **optional, opt-in component**, shipped as
  the literal empty JSON array `[]`. This is deliberately **not** a copy of the pattern
  source's own baseline file — that file snapshots the pattern source's own pre-existing lint
  debt, which is meaningless (and would be actively misleading, and on most real codebases
  would make the ratchet fail out-of-box) for a fresh adopter. The `.template` suffix means
  neither file ships live: `pytest` does not collect `test_leanness_ratchet.py.template`, and
  the empty `leanness_baseline.json.template` is never read by a live test. Activating the
  ratchet means renaming both files back (dropping `.template`) AND regenerating the baseline
  from the adopter's OWN current codebase — never shipping the empty template baseline as-is
  once the test is live, since an adopter repo with any pre-existing C901/SIM/PLR-family
  violations would then fail immediately. Concrete steps: `files/tests/README.md`.

## ADAPT notes

- **`{{SHARED_CODE_HOME}}` / scan-root retargeting.** The ratchet template's `SELECT`
  scanner already defaults to a generic `["src/"]` path list (not a project-specific one)
  — no code change is needed if your project's shared/application code lives under
  `src/`. If it doesn't, retarget the `["src/"]` argument passed to `violation_identities(...)`
  at its three call sites in `test_leanness_ratchet.py` (`_write_baseline`, the
  `test_leanness_ratchet_no_new_violations` test, and the negative-control tests) — do this
  retargeting on your activated copy, after renaming `test_leanness_ratchet.py.template` to
  `test_leanness_ratchet.py` (see `files/tests/README.md`) — to your own scan root. Module
  `21-pipeline-skills`'s REVIEW-full Step 2b(iii)(a) (the duplication check, always installed,
  unconditional) names the SAME canonical shared-code home via the `{{SHARED_CODE_HOME}}`
  placeholder in its own remediation message — if you retarget one, retarget the other to
  match, so the duplication-check's remediation advice and the ratchet's own scan root point
  at the same place.
- **Ruff resolution / non-`.venv` layouts.** The ratchet resolves its `ruff` binary via a
  fallback chain — `$RUFF_BIN` env override, `.venv/bin/ruff` (POSIX venv),
  `.venv/Scripts/ruff.exe` (Windows venv), then `shutil.which("ruff")` (PATH) — instead of one
  hardcoded path, so it works across OSes and non-`.venv` installs (uv/poetry/conda/system
  Python). If your project doesn't use a `.venv`-based install, set `RUFF_BIN` to the exact
  path before running the ratchet (see `files/tests/README.md`); no code edit is needed. If
  none of the candidates resolve, the ratchet fails LOUD (`RuntimeError` naming every candidate
  tried) rather than silently skipping.
- No other ADAPT placeholder exists in this module — the three prose slices are
  structurally generic.

## Deny-list self-check (Global Constraint 6)

All five files in this module (`README.md`, `claude-md-block.md`,
`files/docs/harness/26-code-discipline.md`, `files/tests/test_leanness_ratchet.py.template`,
`files/tests/leanness_baseline.json.template`) were checked against the kit's expanded deny-list
(the project/vendor names, domain-specific field names and abbreviations, database
filenames, and project-specific path prefixes named in this plan's Global Constraint
6) — zero hits. One project-specific example path and class name that had leaked into a
copied test's illustrative data was replaced with an invented, domain-neutral
equivalent. `leanness_baseline.json.template` ships as `[]`
specifically because the pattern source's own baseline file is where several deny-listed
project-specific paths would otherwise have leaked in verbatim.

## Interfaces

- Module `27-data-handling`'s synthetic-test-data-only rule wires into this module's
  test-first tests whenever module `24-skill-delivery` is NOT installed (Q6 = no) — see
  `27-data-handling/README.md`'s "Interfaces" section. This module is guaranteed present
  whenever 27 is, via the Q5 STANDARD floor (27 always co-installs at STANDARD+; this
  module is STANDARD+'s own unconditional member), so that wiring is never vacuous.
- Module `21-pipeline-skills`'s REVIEW-full Step 2b(iii)(b) is conditional on this module's
  optional leanness-ratchet template being installed **and activated** — the check keys on
  the live `tests/leanness_baseline.json` / `tests/test_leanness_ratchet.py` (no `.template`
  suffix). If an adopter's repo only has the shipped `.template` files (not renamed/opted
  in), or has neither, that sub-check cleanly skips.
