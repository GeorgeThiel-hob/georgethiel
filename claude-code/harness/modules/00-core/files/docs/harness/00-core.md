# Harness detail — 00-core hard rules, memory conventions, Definition of Done

Full text and rationale for the eight universal hard rules summarized in CLAUDE.md's
`<!-- HARD-RULES -->` slot, plus the memory-log convention and the Definition-of-Done
shape every rigor profile installs. Read this before treating any hard rule as
boilerplate — each one exists because a specific failure mode kept recurring across
projects.

---

## 1. Never assume — confirm with research, analysis, or data

**Rule:** before using any factual claim as the foundation for downstream work, verify
it. Acceptable verification: reading the primary source (code, config, a document),
running a query against real data, or an independent reviewer's confirmation.
Unacceptable: "this seems right," "I recall this," "the summary said so."

**Why:** a plausible-sounding claim, treated as settled fact and built upon, is the
single most common root cause of wasted work across projects that use this harness. The
claim that "feels obvious" is the highest-risk case — that is exactly the claim worth
interrogating, not skipping.

**How to apply:** label every load-bearing claim with one of four confidence tags —
**Verified** (cite the file:line, query result, or primary source), **Estimated**,
**Assumed**, or **Unknown**. A claim tagged Assumed or Unknown blocks the next action
until it is verified or explicitly escalated.

## 2. Always invoke systematic-debugging for bugs — never brainstorming

**Rule:** any unexpected behavior, error, or test failure routes to a systematic
debugging procedure — reproduce, isolate, one hypothesis at a time, empirical
confirmation — before any fix is proposed. A creative/exploratory process (the kind used
for designing a new feature) is the wrong tool for a bug; it invites chasing a plausible
but wrong hypothesis instead of the one the evidence actually supports.

**Why:** ad-hoc debugging burns effort chasing wrong hypotheses. The failure mode this
guards against: a session spends most of its effort on a hypothesis that "feels" right,
while the actual root cause was visible from the very first piece of evidence (a diff, a
log line, an error string) — a class of failure that recurs whenever the first
plausible-sounding theory is pursued to the exclusion of everything else.

## 3. Build a deterministic feedback loop before hypothesising

**Rule:** before forming hypotheses about any bug, build a fast, repeatable, pass/fail
signal that reproduces the bug in the **real** environment where it occurs — not a
simulated or manual stand-in for that environment. State what the loop is and what
signal it emits before hypothesising. If no such loop can be built, report the specific
blocker before proceeding — do not hypothesise into the dark.

**Why:** the cheapest accelerant to a debugging session is a loop that tells you,
immediately, whether a change helped — without it, each hypothesis costs a full
investigation cycle to test.

## 4. Never claim "fixed" without environment verification

**Rule:** "fixed" means confirmed in the actual environment where the bug occurred — not
in a manual simulation of it. If the real environment cannot be exercised in the current
session (for example, a fix that needs a restart or a deploy to take effect), say so
explicitly rather than declaring success: "committed, needs \[restart/deploy/etc.\] to
confirm."

**Why:** a fix that passes in a simplified simulation can still fail once it runs in the
real environment, because the simulation silently omitted the exact condition that
caused the bug. Each premature "fixed" claim that later turns out false costs more than
the honest "not yet confirmed" would have.

## 5. Verify before declaring complete

**Rule:** before claiming work is complete, fixed, or passing, run the actual
verification command(s) and read the output. Evidence before assertions, always — a
passing memory of what should happen is not the same as a command that just ran and
printed a result.

**Why:** this closes the gap between "I believe this works" and "I ran it and it worked."
The two are easy to conflate under time pressure; conflating them is how broken work
ships as "done."

## 6. Update the lessons log after mistakes

**Rule:** after any owner correction, review finding, self-caught error, test failure
traced to a wrong assumption, or realized design mistake, add one row to a lessons log
with four columns: **Date**, **Category** (e.g. Analysis / Architecture / Code / Data /
Config / Process / Testing), **Mistake**, **Lesson**. When a lesson recurs, or proves
universal across tickets, promote it out of the log and into a permanent hard rule or
convention doc.

**Why:** without a durable log, the same category of mistake repeats across sessions —
each new session starts blind to what the last one already learned the hard way. The log
is how a project accumulates institutional memory across sessions that otherwise share
no state.

## 7. Verify ticket/ID non-collision before naming

**Rule:** before assigning any new ticket or work-item ID, enumerate existing IDs from
every authoritative source (commit history, issue tracker, ticket/spec directories).
Choose an ID that does not collide — either the next number in an existing family, or a
new prefix that avoids any ambiguity.

**Why:** reusing an ID silently overwrites or conflates earlier history — prior specs,
plans, decisions, and cross-references tied to that ID become ambiguous or corrupted.
This is cheap to prevent and expensive to untangle after the fact.

## 8. Communication style

**Rule:** lead with the answer, then the reasoning — never bury the conclusion under a
wall of preamble the reader has to wade through to find it. Cite a source (`file:line`, a
command's output, a doc section) instead of restating it in prose. Match the explanation
to the reader's actual expertise: keep the substance (the variables, the math, the
precise terms) but spell out any shorthand or abbreviation the first time it appears, so
a reader who is skilled but unfamiliar with this specific project can follow without
guessing. Put wide or tabular data in a fixed-width code block rather than a prose table.

**Why:** a reader evaluating a finding or a proposed change needs the conclusion first so
they know what they're being asked to agree with — reasoning that arrives before the
conclusion reads as suspense, not rigor. Citing a source instead of re-describing it keeps
the writeup checkable: the reader can open the exact line instead of trusting a paraphrase.
Unglossed shorthand silently excludes a reader who knows the general subject but not this
project's private vocabulary, and a rendering surface that reflows or wraps text can turn
a table into an unreadable jumble, so tabular data is safest in a format that always
renders as written.

---

## Memory conventions

Record decisions and mistakes durably, outside the ticket in front of you, so later
sessions inherit context instead of re-deriving it:

- Keep a **lessons log** — one table with columns Date / Category / Mistake / Lesson
  (see rule 6 above). Scan it for entries relevant to the current work before starting.
- Keep a **decisions record** — settled architectural or process decisions, each with the
  decision, the rejected alternative, and the condition under which it should be
  revisited. Treat entries here as load-bearing: don't silently re-litigate a settled
  decision without new evidence.
- When a lesson or decision recurs enough to stop being project-specific trivia and
  starts being a general rule, promote it: move it out of the log/record and into this
  project's permanent hard-rule or convention documentation, so it is enforced going
  forward rather than merely logged.

## Definition of Done (shape)

Every rigor profile installs some version of this checklist; the exact commands come
from the ADAPT substitutions (`{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPE_CMD}}`) bound at
install time from the stack the member described:

1. `{{TEST_CMD}}` — zero failures
2. `{{LINT_CMD}}` — clean
3. `{{TYPE_CMD}}` — zero errors
4. Acceptance criteria confirmed with file:line or test name — not by recollection
5. Affected docs updated — the commit explains WHAT changed and WHY

A change is not "done" until every applicable line above has actually been run and its
output checked, per rule 5 above.
