# Module 10 — hooks-base

**Purpose:** the fail-open `PreToolUse` dispatcher plus its lib scaffolding — the
substrate every other hook-carrying module (20, 22, 23, 30) plugs into. This module
ships no checks of its own; it ships the mechanism every other module's checks are
called through.

**Dependencies:** none. This is the base of the hook stack — no module below it.

**ADAPT notes:** none. The dispatcher and its lib scaffolding are structurally generic —
no project-specific value for an adopter to fill in.

## What ships here

- `files/dot-claude/hooks/run_python.sh` — verbatim copy of the cross-platform
  Python 3 launcher. Byte-identical to source; no changes.
- `files/dot-claude/hooks/lib/__init__.py` — verbatim copy. Defines `HookResult`
  (the `(allow, block_message)` namedtuple every check function returns) and
  `log_hook_error` (the shared fail-open diagnostic logger). This is the base
  every other hook lib file imports — module 23 (`23-guards`) declares a hard
  README dependency on this module for exactly that reason.
- `files/dot-claude/hooks/lib/phases.py` — **kit-variant, not verbatim.** Single
  source of truth for advisor/second-opinion-seat call phase token constants
  (`BRAINSTORM`/`SPEC`/`PLAN`/.../`SHIP`). The source's post-deploy-verification
  phase constant is dropped: this kit excludes the deploy-verification gate
  entirely (see `modules/excluded/README.md`), so that phase token would be
  dead — defined, added to `ALL_PHASES`, but never produced by any advisor
  call site or consumed by any gate in this kit. Every remaining constant and
  `ALL_PHASES` itself are otherwise byte-identical to source.
- `files/dot-claude/hooks/pretooluse_dispatcher.py` — **kit-authored variant, NOT
  a verbatim copy.** See "Dispatcher variant" below for the exact deltas.

## Dispatcher variant — the three named deltas (AC-6)

Read from `.claude/hooks/pretooluse_dispatcher.py` as the base. Exactly three changes
were applied, and nothing else — every other dispatch branch is structurally
identical to source.

**AC-6 delta names:** "import-guarded dispatcher, not verbatim", "dead external-service MCP dispatch-branch strip (an excluded module's check)", and "dead-registration strip (`bash_checks`/`read_checks`/`evidence_store_guard`)".

1. **Import-guarded dispatcher, not verbatim.** Every `from lib.X import
   check_fn` at the top of the source file is replaced with a call to a local
   `_maybe_register(import_path, check_fn_name)` helper, wrapped in
   `try/except (ImportError, AttributeError): pass`, and the resulting function
   (if found) is stored in a module-level `_CHECKS` registry. Every call site in
   `dispatch()` looks the function up with `_CHECKS.get(name)` instead of calling
   an imported name directly, and treats `None` as "this check doesn't apply in
   this install" rather than an error. This is what makes an unselected/absent
   kit module's checks simply not register instead of crashing the dispatcher —
   the mechanism every other hook-carrying module's presence-or-absence safety
   depends on. Two distinct absence cases both degrade safely through the same
   guard: (a) the whole lib file is missing because the adopter didn't install
   that module — `import_module` raises `ImportError`; (b) the lib file IS
   installed but this kit's variant only ships a subset of the source file's
   functions (e.g. module 20's `task_checks.py` kit variant deliberately drops
   `check_ac_id_prefix` and `block_finishing_branch_skill` — see
   `20-tier-system/README.md`) — `getattr` on the present-but-incomplete module
   raises `AttributeError`. Both are caught in the same `_maybe_register`, so a
   partial or wholly-absent optional module can never prevent this dispatcher
   itself from loading.
2. **Dead external-service MCP dispatch-branch strip.** The source's top-level
   tool-name-prefix branch (source `pretooluse_dispatcher.py:181-183`) guarding
   calls into one specific, excluded external-service MCP server, and its
   accompanying optional-lib import, are removed entirely — not guarded,
   REMOVED — because this kit ships no check for that tool-name pattern at all
   (see the credit-metered-external-API entry in `modules/excluded/README.md`
   for why). Unlike the checks import-guarded under delta 1, this whole branch
   will never register in ANY kit install, ever, so it is deleted rather than
   left as an always-inert guarded no-op.
3. **Dead-registration strip.** The source's `_maybe_register` calls for
   `bash_checks.block_debug_log_commits`, `bash_checks.block_inline_git_reads`,
   `evidence_store_guard.block_evidence_store_bash_write`,
   `evidence_store_guard.block_evidence_store_file_write`, and
   `read_checks.block_committed_plan_reads` are removed, same class as delta 2: no
   module this kit ships carries a `bash_checks.py`, `read_checks.py`, or
   `evidence_store_guard.py` lib file, so these five registrations would sit
   forever-inert behind `_maybe_register`'s `ImportError` guard in every one of the
   kit's 9 rigor×routing combinations. Two dispatch branches became **fully** dead
   as a consequence and are removed outright rather than left as empty shells: the
   `Bash` branch (all three of its checks were among the five stripped) and the
   `Read` branch (its only check was among the five stripped) — both tool names
   now fall through to the unchanged final unknown-tool `{"decision": "allow"}`,
   identical runtime behavior to the branch existing and finding every check
   absent. The `Edit`/`Write`/`MultiEdit` branch keeps its structure: only the
   `block_evidence_store_file_write` lookup (one of the five) is removed from the
   front of that branch — `check_reexec_directives`, `check_circular_evidence`,
   and `check_claim_binding` are all live checks this kit does ship, so that branch
   stays.

Every other dispatch branch (`Task`/`Agent`, `Edit`/`Write`/`MultiEdit`, `Skill`, and
the final unknown-tool fallback) preserves the source's structure, comments, and
short-circuit order — only the "call the imported name directly" step became "look
the name up in `_CHECKS` and skip cleanly if absent."

## `settings-fragment.json`

`settings.json` is assembled at install by merging every selected module's
`settings-fragment.json` (spec §9 10-hooks-base note) — this module contributes
only the `PreToolUse` entry pointing at `run_python.sh` + `pretooluse_dispatcher.py`;
module 23 contributes the standalone `Stop`/`SubagentStop` entries in its OWN
fragment (see `23-guards/README.md`). This module's single `PreToolUse` entry uses
a catch-all matcher (`.*`) so that adding a new dispatcher-routed check inside
`dispatch()` — the pattern every other hook-carrying module follows — never
requires a new `settings.json` entry; only `_maybe_register` calls need to change.

## CLAUDE.md block

This module ships **no CLAUDE.md block** — it is pure mechanism (a dispatcher +
lib scaffolding), invisible to the member once installed, with no rule text a
human needs to read.
