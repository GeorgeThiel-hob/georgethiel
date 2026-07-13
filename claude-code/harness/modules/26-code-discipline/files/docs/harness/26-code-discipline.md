# Harness detail — code discipline

Module `26-code-discipline` is a **kit-authored composition** of three slices plus one
policy statement, each independently sourced and independently labeled — they are not
blended into one undifferentiated "coding standards" paragraph. This detail doc carries
the full text of all three slices and the policy statement; `claude-md-block.md` stays a
short pointer digest given the combined length.

## Slice 1 — naming, logging, error handling, SQL safety, tagged debug logs

**Source:** the generic subset of a pattern-source code-conventions
document. Carried over as-is where the rule is project-agnostic; dropped entirely where
the source rule named a specific language runtime, financial-precision handling, an
async/synchronous-client bridging pattern, or a signal-data field convention — those are
project-bound and out of scope for a general-purpose kit. Nothing below is a full section
retitled; each rule was individually checked against that boundary before inclusion.

### Naming

- Modules: `snake_case.py`, Classes: `PascalCase`, Functions/vars: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`, Tests: `test_<what>_<scenario>`.

### Logging

- Use the standard logging module, not `print()`. One logger per module:
  `logger = logging.getLogger(__name__)`.
- Levels: DEBUG (data values), INFO (operations), WARNING (recoverable), ERROR
  (failures), CRITICAL (system).
- Format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.

### Error handling

- Never `except: pass`. Log errors with context. Retry with exponential backoff
  (a small fixed cap, e.g. 3 attempts) for operations that can transiently fail.
- A single failing component (one fetcher, one worker, one integration) must not be
  allowed to crash the whole process — isolate its failure mode.

### SQL safety

- **Always use parameterized queries** — never f-strings or `.format()` to build SQL:

  ```python
  # WRONG — SQL injection risk
  cursor.execute(f"SELECT * FROM orders WHERE id = '{order_id}'")

  # CORRECT — parameterized
  cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
  ```

- This applies to every `execute()` call in every module. No exceptions.

### Tagged debug logs

Temporary diagnostic logs added while debugging should be tagged `[DEBUG-<4hex>]` — a
random 4-hex tag chosen per investigation, e.g.:

```python
logger.debug("[DEBUG-a4f2] user_id=%s count=%s", uid, n)
```

The tag makes every temporary line greppable and impossible to lose. Before committing,
remove them all:

```bash
grep -rn '\[DEBUG-' <your-src-dir>/ <your-test-dir>/
```

This is a documentation convention in this module, not a mechanically-enforced gate — no
hook in this kit currently scans commits for a stray `[DEBUG-` line. An adopter who wants
that enforcement writes their own PreToolUse Bash-content check (see `10-hooks-base`'s
import-guard pattern for how to add one without risking a crash on a missing module).

## Slice 2 — lean-code principles

**Provenance:** kit-authored, NO direct pattern source (grep-verified 2026-07-06: no prior
document states these principles as such — they are standard software
practice, written fresh for this kit). Labeled exactly like module `24-skill-delivery`'s
fixture-testing loop, which carries the same "authored fresh, no proven source" honesty
label.

- **Small functions.** A function should do one thing describable in one sentence. When a
  function needs "and" to describe what it does, it is a candidate to split.
- **No speculative abstraction.** Do not build a parameter, a config flag, or a plugin
  seam for a use case that does not exist yet. Add the seam when the second real caller
  shows up, not in anticipation of a hypothetical third.
- **Comment discipline.** A comment explains *why*, not *what* — the code already says
  what it does. A comment that only restates the next line in English is noise; delete it
  or replace it with the reasoning the code itself cannot carry (a tradeoff made, a
  constraint being worked around, a non-obvious invariant being preserved).

## Slice 3 — architecture vocabulary

**Source:** a pattern-source architecture-vocabulary reference document —
near-fully generic; only its project-specific illustrative file:line examples are
scrubbed (replaced with invented, domain-neutral ones below; the term definitions and the
deletion test are unchanged).

**Terms:**

- **module** — a scale-agnostic unit with a defined interface and a hidden implementation.
  Can be a single function, a class, or a whole file — scale doesn't decide whether
  something qualifies, a callable surface plus hidden internals does.
- **interface** — everything a caller must know to use a module correctly: parameter
  names, types, preconditions, return shape. Not the code that produces the result.
- **implementation** — the code inside a module that fulfills the interface contract.
  Callers don't depend on it; it can change without the caller rewriting, as long as the
  interface contract holds.
- **depth** — large capability behind a small interface. A measure of leverage, not line
  count: a 500-line module with a 50-line interface is deep; a 10-line pass-through with a
  9-line interface is shallow.
- **seam** — a place in the design where behavior can be altered without editing that
  place. Created by parameterization, dependency injection, or protocol indirection.
- **adapter** — a concrete object that satisfies an interface at a seam, making one thing
  look like another to the consumer on the other side.
- **leverage** — capability per unit of interface a caller must learn. High leverage means
  a caller accomplishes a lot by knowing a little.
- **locality** — the property of changes and fixes being concentrated in one place. High
  locality means adding a rule or fixing a bug touches one file, not every caller.

**Example (invented, domain-neutral):** a `PriceFormatter.render()` module with a
one-method interface (`amount`, `currency_code` in; a formatted string out) is deep if it
hides locale rules, rounding conventions, and symbol placement inside — callers never see
that logic. If three call sites each hand-roll their own rounding and symbol placement
instead of calling it, the module has "leaked" — the deletion test below is how you catch
that.

**The deletion test:** imagine deleting the module. If complexity vanishes across
callers, it was a pass-through — absorb it, don't ship it. If complexity reappears across
N callers, it earned its keep — keep it. Apply this test to every NEW module proposed in a
spec or plan, citing the callers either way.

**Divergent interface shapes before elaborating one:** when a design proposes a new module
or a new public interface, sketch 2-3 divergent shapes first — different signatures,
parameter/return types, error modes — and list ALL of them before elaborating any single
one, so the first shape sketched doesn't silently anchor the rest. Then apply the deletion
test to each shape and pick the deepest — the one hiding the most capability per parameter
and return type a caller must learn.

**Depth over surface:** between two designs that solve the same problem, prefer the one
that lets a caller do the most while needing to understand the least, even if that means a
larger implementation behind a smaller interface.

## Test-first policy

This is a **kit policy choice, not a straight port** — the installed CLAUDE.md mandates
invoking a test-driven-development skill (a Superpowers-plugin prerequisite,
`superpowers:test-driven-development`) for code work: write the failing test first, then
the implementation that makes it pass. The pattern source's own rule is
tests-*required*, not test-*first* (tests must exist before merge; the plugin dependency
this module pulls in is stricter — tests must exist before the implementation). Adopters
without the Superpowers plugin installed should read this as "tests required before merge"
and treat the strict test-first ordering as aspirational, not gated.

## Optional component — the leanness-ratchet test template

See `README.md` and the opt-in activation steps in `files/tests/README.md`, plus the
shipped templates `files/tests/test_leanness_ratchet.py.template`
+ `files/tests/leanness_baseline.json.template`. Once activated (renamed back to
`.py`/`.json` with an adopter-generated baseline), this is what makes module
`21-pipeline-skills`'s REVIEW-full Step 2b(iii)(b) (the leanness baseline-bump guard)
actually engage instead of cleanly skipping.

This module is the **"lean, simple, robust, readable" axis**: prose discipline in the
three slices above, with an optional mechanical backstop (the ratchet template) via
REVIEW's Step 2b(iii).
