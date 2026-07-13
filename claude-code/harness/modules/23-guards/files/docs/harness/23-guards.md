# Harness detail — the guard pack

Full import-closure map, the WARN-first-before-BLOCK rationale, and a concrete
`reexec:` directive example. Read this before treating any of this module's
four checks as a black box — three are WARN-/log-grade, one is BLOCK-grade,
and the difference is deliberate, not an oversight.

## WARN-first-before-BLOCK — the pattern for introducing any new gate

Shipping a gate at BLOCK grade from day one gives it no measurement period to
catch false positives before it costs someone a blocked write. The fix: ship
the check as a non-blocking WARN first — log every trigger to a dedicated
log file and let the write proceed regardless — then look at the accumulated
log after real usage and decide whether the false-positive rate is low enough
to promote the check to BLOCK. A gate that has never been measured has no
basis for blocking anyone.

Of this module's four checks, three are still in the WARN/log phase:

- `claim_binding_guard.py` (`check_claim_binding`) — WARN-grade, non-blocking.
- `circularity_guard.py` (`check_circular_evidence`) — WARN-grade, non-blocking.
- The confidence-label scan inside `subagentstop_log.py`
  (`maybe_log_label_misses`) — log-only, no warn print, no block.

One check has already earned promotion out of that phase:

- `stop_citation_guard.py` — **BLOCK-grade.** Its default `CITATION_GUARD_MODE`
  is `"block"`, and it BLOCKS a Stop event once a turn accumulates
  `MIN_FLAGS_TO_BLOCK` (default 2) distinct flagged lines, bounded by a
  3-loop ceiling so it can never wedge a session shut. This is the mature
  exception the pattern describes, not a contradiction of it — it earned
  BLOCK grade through its own prior measurement period before this kit
  existed.

## Import-closure map

Every file this module ships, and what each one imports:

| File | Imports | stdlib-only? |
|---|---|---|
| `stop_citation_guard.py` | `lib.claim_detector`, `lib.transcript_utils` | Yes |
| `subagentstop_log.py` | `lib.claim_detector` | Yes |
| `lib/claim_detector.py` | `re`, `dataclasses` | Yes |
| `lib/transcript_utils.py` | `json`, `collections` | Yes |
| `lib/post_edit.py` | `pathlib` | Yes |
| `lib/claim_binding_guard.py` | `lib/__init__` (module 10), `.claim_detector`, `.post_edit`, `.reexec_guard` | No — needs module 10 |
| `lib/circularity_guard.py` | `lib/__init__` (module 10), `.post_edit` | No — needs module 10 |
| `lib/reexec_guard.py` | `lib/__init__` (module 10), `.post_edit` | No — needs module 10 |

`lib/__init__.py` (`HookResult`, `log_hook_error`) is shipped by module
`10-hooks-base`, never by this module — see the README's "Dependencies"
section for why this is a hard, not optional, dependency.

## Two standalone hooks — the full closure MUST ship together

`stop_citation_guard.py` (Stop) and `subagentstop_log.py` (SubagentStop)
register via this module's own `settings-fragment.json`, not via the
dispatcher-routed `_maybe_register` guard module `10-hooks-base` provides for
every other check in the kit. That guard is what lets an unselected optional
module's checks simply not register instead of crashing the dispatcher — but
it only protects dispatcher-routed checks. These two events are wired
directly in `settings.json`, so if any file in the closure above is missing,
the hook crashes at load time instead of degrading gracefully. Ship all of
it, every time this module is selected.

## A concrete `reexec:` directive example

The convention this module's `reexec_guard.py` enforces, shown as one real
example rather than an abstract description — a claim that a made-up token
does not appear anywhere under this doc directory:

```
<!-- reexec:absent pattern="EXAMPLE_TOKEN" path="docs/harness" -->
```

At Write/Edit/MultiEdit time, the guard re-runs
`grep -rIFn -e "EXAMPLE_TOKEN" -- docs/harness` against the current tree and
compares the result to the claim. Zero matches → the claim holds, the write
proceeds. One or more matches → clean contradiction, the write BLOCKS with a
message naming the exact grep that failed. This is the recompute-and-compare
primitive in full: the directive is never trusted at face value, only ever
re-verified against the tree as it exists right now.
