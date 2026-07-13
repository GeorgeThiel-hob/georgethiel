# The interview — resolving rigor, routing, and the module set

This is the script `START-HERE.md` step 3 sends you to. Its job is to turn the
member's answers to up to nine questions (one, Q4, may be skipped when a
provably-moot condition holds — see the resolution algorithm's "Skip logic") into
exactly one rigor profile, one routing profile, and a set of environment flags — the
inputs step 4 of the install flow feeds into the resolution algorithm below to pick
the modules that get installed.

## How to run this interview

Ask Q1 through Q9 **one at a time**, in order. After the member answers, read the
answer back to them in your own words and get explicit confirmation before moving to
the next question. Never batch two questions into a single message, and never skip a
question because an earlier answer *seems* to make it obvious — Q9's read-back is the
safety net, but it only works if every prior answer was actually confirmed
individually on its own.

**One named exception, spelled out in full below:** the resolution algorithm documents
exactly one provable skip condition — Q4 is skipped when Q1 has already resolved to
FULL rigor, because the saturation clamp makes Q4's answer mathematically incapable of
changing the outcome (see "Skip logic" under the resolution algorithm). That is the
only question this interview ever skips, and only for that stated reason — never on
judgment, never because a different answer "seems obvious." Every other question is
always asked, in full, every time.

---

## Q1 — "What will you build here?"

Free-form answer. Classify it into exactly one of three categories using the rubric
below, then read your classification back to the member and get their confirmation —
this is a judgment call, not a keyword match, so the member's confirmation is the real
check.

**skills-only** — a Claude Code skill or a small piece of reusable instruction-following
content; no persistent app, no database, no scheduled execution of its own.
- "a Word-doc formatting skill"
- "a meeting-notes summarizer"

**mechanical-automation** — a scripted or no-code automation that runs on a trigger or
schedule, touching files or other systems, but with no user-facing app or database of
its own.
- "a Power-Automate flow that files expense reports"
- "a scheduled script that reconciles two spreadsheets"

**code-heavy** — a persistent application, service, or pipeline with real users or a
database and an ongoing maintenance surface.
- "a customer-facing web app"
- "a data pipeline with a persistent database"

**Mixed-project rule:** mixed projects take the highest-rigor deliverable's profile —
if the answer describes a bundle spanning categories, classify by the single
highest-rigor piece in it, not by the average or the majority.

This answer sets **Q1_base**, the starting rigor level the resolution algorithm below
composes with Q4 and Q5.

Why this matters: rigor is process weight — the wrong level either wastes effort on a
low-stakes deliverable (over-scoped) or leaves a genuinely risky project unverified
(under-scoped).

---

## Q2 — "Which Claude plan is this account on? (Pro / Max 5x / Max 20x)"

Binds the **routing profile** — which models get dispatched for which role (spec
authoring, implementation, review, and so on).

Why this matters: your plan sets the affordable model ceiling; the wrong routing
profile either burns through your usage window faster than the work justifies, or
under-uses a bigger budget you're already paying for.

---

## Q3 — "GitHub repo or local-only folder?"

Binds the ship and ticketing variants: the GIT-github ship skill plus GitHub-issue
ticketing for a GitHub repo, or the GIT-local ship skill plus a local `tickets/` folder
for a local-only folder.

Why this matters: this determines which skill variant gets installed — there is no
universal ship mechanism that works identically both ways.

---

## Q4 — "If an output of this project is wrong, what breaks? (money / compliance /
irreversible data vs. redoable inconvenience)"

**Before asking this question, check skip condition S1 in the resolution algorithm
below.** If Q1 already resolved to FULL rigor (a code-heavy answer), skip Q4 entirely —
do not ask it — and record "Q4 — skipped, rigor already pinned at FULL by Q1" for the
Q9 read-back. Otherwise, ask it normally.

This is the risk axis. It may bump the resolved rigor one tier up — call this
**Q4_fires** when it does.

**Risk-bump rule, in full:** an answer naming money, compliance exposure, or
irreversible data loss bumps LIGHT → STANDARD or STANDARD → FULL. An answer describing
a redoable inconvenience does not bump anything. In one line: rigor follows blast
radius, not deliverable type alone — a "skills-only" answer to Q1 can still carry a
high-stakes failure mode here.

Why this matters: a simple-looking deliverable can still have a high-stakes failure
mode that Q1's classification alone would never surface.

---

## Q5 — "Will this project process personal, client, or financial data (documents
containing names, account numbers, salaries, medical info…)?"

This is the PII gate. It is a floor, not a scaling factor — read the distinction
carefully, because it is easy to conflate with Q4's bump.

**PII gate, in full:** a "yes" answer hard-floors rigor at STANDARD — LIGHT is removed
from the resolution entirely for this project, with no override — and auto-installs
the data-handling module (`27-data-handling`) at **any** resolved profile, LIGHT
included. Rationale: rigor profiles scale process-verification depth for the
deliverable itself; data sensitivity is an independent axis, because a trivially
simple skill can still process highly sensitive documents. That is why this gates
rather than scales, and why LIGHT stays available for genuinely non-sensitive work
answered "no" here.

Why this matters: mishandled personal data is a different failure class than a wrong
spreadsheet formula — it doesn't scale down just because the project around it is
simple.

---

## Q6 — "Will deliverables be used by people on the Claude desktop app?"

A "yes" answer binds the skill-delivery module (`24-skill-delivery`).

Why this matters: desktop-bound skills can only use what the desktop surface offers
(uploads, conversation, artifacts) — no repo tools, no hooks, no subagents. That is a
different self-containment bar than the tool-driven building harness this kit installs
for everything else, and the deliverable has to be authored to that bar from the
start.

---

## Q7 — "I'll default this project to a Python stack — pytest / ruff / mypy — unless
it's actually a different language. Is that right, or is this something else?"

Most member projects turn out to be plain Python scripts, and a member frequently
doesn't have their own test/lint/type commands memorized. So lead with the default and
only branch if the answer is "no":

- **Default path (the member confirms Python, or doesn't know):** accept the default —
  do not ask the member to enumerate their own commands. Bind the Definition-of-Done
  ADAPT values to the standard Python commands: `{{TEST_CMD}}` = `pytest`,
  `{{LINT_CMD}}` = `ruff check .`, `{{TYPE_CMD}}` = `mypy .`. A member who doesn't know
  their own stack should never be made to reconstruct it from memory just to get past
  this question.
- **Branch path (the member says a different language, or names different tooling for
  the same commands, e.g. `flake8` instead of `ruff`):** ask for that language's or
  tool's equivalent test / lint / type commands and bind those instead. If there is no
  code at all, bind all three ADAPT values to `N/A`.

Binds the ADAPT values for the installed Definition-of-Done section.

Why this matters: the installed Definition-of-Done section needs real test / lint /
type commands to mean anything — not the placeholder tokens the kit template ships
with before ADAPT substitution. Leading with the Python default — instead of an
open-ended "what's your stack?" — matches what most members actually run and removes a
question that would otherwise stall on "I don't know."

---

## Q8 — Optional add-ons

Offer two independent add-ons; either, both, or neither may be selected:

- **Reasoning playbooks** (module `30-reasoning-playbooks`) — offered only on Max 5x
  and Max 20x plans (Q2-gated). Requires STANDARD+ rigor (its module-22 dependency
  isn't installed at LIGHT) — if the member chose LIGHT, this add-on is skipped.
- **Debate tools** (module `31-debate-tools`) — offered on **any** plan. Explain what
  this actually is, in plain English, before the member decides:
  - **COUNCIL** is stochastic multi-agent consensus: it spawns several (roughly 5-10)
    parallel analyst agents, each given a distinct persona/perspective, all working the
    same question independently and at the same time; their answers are then aggregated
    into one consensus view plus the specific divergences and outlier opinions. Good
    for surfacing blind spots a single pass would miss.
  - **DEBATE** is round-robin multi-model debate: several agents argue the same
    question in turns across multiple rounds, each seeing and responding to the others'
    positions — conceding, holding, or countering — converging toward an agreed answer
    (or explicitly failing to converge). Good for stress-testing a question that has
    genuine competing answers, not just one "best" answer to find.
  - **When they help:** a wide design space where several plausible approaches need to
    be raced against each other, or a decision that's expensive to get wrong (an
    architecture choice, a strategy change, anything hard to reverse) — not routine,
    single-answer questions.
  - **Cost:** roughly 5-10x a normal exchange, because each run dispatches that many
    parallel or sequential agent calls. Read this token-cost warning aloud to the
    member **verbatim** before they decide: "one run can consume a large share of a Pro
    usage window — reserve for decisions that are expensive to get wrong."

Why this matters: these are opt-in brainstorm boosters, not mandatory pipeline steps —
declining both costs the member nothing. A member who understands what COUNCIL and
DEBATE actually do and actually cost can make a real opt-in decision instead of
guessing from the module name alone.

---

## Q9 — Read-back and final confirmation

Read back, in one message: all prior answers — including an explicit note if Q4 was
skipped under skip condition S1, and why — the resolved rigor profile, the resolved
routing profile, and the full module list the resolution produces. The member confirms
this summary before you write anything. This is the last question, not a ninth
independent input — it exists purely as the final check.

Why this matters: this is the last chance to catch a misclassification before any file
gets written to the destination repo.

---

## Resolution algorithm

This is the only legal way to compose Q1's base classification, Q4's risk bump, and
Q5's PII gate into one rigor tier. It is owner-pinned (2026-07-06); do not re-derive or
restate a different composition anywhere else in this kit, in an installed CLAUDE.md,
or in any doc that references it — this is the single source of truth, reached by path
from `START-HERE.md` step 4.

> **Fast path vs. authority:** `profiles/resolution-table.md` mirrors this section's
> 12-cell hand trace plus the Q5/Q8 conditionals into one lookup table, so the
> installing session can resolve rigor + modules from a single read instead of walking
> the algorithm by hand every time. That table is the fast path; this section is the
> rationale and the authority — if the two ever disagree, this section governs and the
> table has a bug.

Rigor tiers, in ascending order: LIGHT, STANDARD, FULL.

The algorithm, reproduced verbatim:

```
rigor = min(FULL, (Q5=yes ? max(Q1_base, STANDARD) : Q1_base) + (Q4_fires ? 1 : 0))
```

Read it in this exact order — the order is load-bearing, not incidental:

1. **PII promotion applies first.** If Q5=yes, floor the base at STANDARD:
   `max(Q1_base, STANDARD)`. A LIGHT base is promoted to STANDARD; a STANDARD or FULL
   base passes through unchanged. If Q5=no, the base passes through unchanged too.
2. **The risk bump reads the already-promoted level**, not the raw Q1 answer. If Q4
   fires, add one tier on top of whatever step 1 produced — not on top of Q1_base
   directly.
3. **The bump saturates at FULL.** `min(FULL, ...)` means a bump applied to an
   already-FULL level has no further effect — there is no tier above FULL to move
   into. This is stated explicitly so no implementer guesses at an "overflow" state
   that doesn't exist.

**Pinned cell (Q1=LIGHT, Q4 fires, Q5=yes) → FULL:** two independent blast-radius
signals compound here — PII promotes LIGHT to STANDARD in step 1, then the risk bump
adds one more tier to FULL in step 2. This is the highest-stakes combination the
interview can produce, and the owner chose maximum protection for it deliberately. All
other eleven cells are order-independent under either reading of the composition; this
algorithm is written down so that exactly one reading exists anywhere in the kit.

### 12-cell hand trace

Every combination of Q1's three possible base levels, Q4's two states, and Q5's two
states, worked by hand against the algorithm above. Read a row by applying step 1,
then step 2, then step 3 to that row's inputs — the two middle columns show the
intermediate values so no step has to be re-derived.

| # | Q1_base  | Q4 (risk bump) | Q5 (PII) | Step 1: post-PII base | Step 2: + bump      | Step 3: resolved rigor |
|---|----------|----------------|----------|------------------------|----------------------|------------------------|
| 1 | LIGHT    | no             | no       | LIGHT                  | LIGHT                | LIGHT                  |
| 2 | LIGHT    | no             | yes      | STANDARD                | STANDARD             | STANDARD               |
| 3 | LIGHT    | fires          | no       | LIGHT                   | STANDARD             | STANDARD               |
| 4 | LIGHT    | fires          | yes      | STANDARD                | FULL                 | **FULL** ← pinned cell |
| 5 | STANDARD | no             | no       | STANDARD                | STANDARD             | STANDARD               |
| 6 | STANDARD | no             | yes      | STANDARD                | STANDARD             | STANDARD               |
| 7 | STANDARD | fires          | no       | STANDARD                | FULL                 | FULL                   |
| 8 | STANDARD | fires          | yes      | STANDARD                | FULL                 | FULL                   |
| 9 | FULL     | no             | no       | FULL                    | FULL                 | FULL                   |
| 10| FULL     | no             | yes      | FULL                    | FULL                 | FULL                   |
| 11| FULL     | fires          | no       | FULL                    | FULL+1 (saturates)   | FULL                   |
| 12| FULL     | fires          | yes      | FULL                    | FULL+1 (saturates)   | FULL                   |

Rows 11 and 12 show the saturation clamp doing its actual job: the raw arithmetic sum
would land one tier past FULL, and `min(FULL, ...)` clamps it straight back down —
there is no tier to overflow into, so the clamp is a no-op in effect but not in the
derivation. Row 6 shows the PII floor doing nothing new when the base is already at or
above STANDARD — it only ever raises, never lowers. Row 4 is the pinned cell: the only
row where both step 1 and step 2 each move the tier, landing exactly on FULL.

### Skip logic — moot questions once rigor is pinned early

The point of the interview is to reach the correct resolved profile, not to ask nine
questions for their own sake. Once Q1's answer resolves Q1_base, check whether a later
rigor-input question is already incapable of changing the resolved tier — asking it
would burn tokens (and, on a Pro-plan account, a meaningful share of the usage window)
without changing the outcome. Exactly one skip condition exists in this algorithm.
**Only skip a question when it is provably moot under the reasoning below — never
invent a new skip ad hoc during a live interview; an unlisted question is always
asked.**

**Skip condition S1 — Q4 is moot when Q1_base = FULL.** If Q1's answer classifies as
code-heavy (Q1_base = FULL), the saturation clamp (`min(FULL, ...)`) means the risk
bump can never move the resolved rigor: FULL + 0 = FULL, and FULL + 1 also clamps back
to FULL. Rows 9-12 of the hand trace above already show this directly — Q4's column
changes across those four rows (no / no / fires / fires) but the resolved rigor is FULL
in all four; no value of Q4 changes row 9-12's outcome. Q4 also has no effect outside
this formula: it does not gate any module install on its own account — module
`31-debate-tools`'s runtime topic classifier shares Q4's blast-radius *schema* (money /
compliance / irreversible-action exposure) to classify whatever topic a member later
asks it to reason about, it does not read the interview's stored Q4 answer (see that
module's README). So when Q1_base = FULL: **skip Q4 entirely.** Do not ask it; record
"Q4 — skipped, rigor already pinned at FULL by Q1" for the Q9 read-back; proceed
straight to Q5.

**Q5 is never skipped, at any Q1_base.** Q5's rigor-floor effect
(`max(Q1_base, STANDARD)`) is a no-op once Q1_base is already STANDARD or FULL (see row
6's note above) — but Q5 has a second, independent effect that has nothing to do with
rigor: it gates the `27-data-handling` module install at **any** resolved profile,
including a Q1_base = FULL project. That module decision cannot be derived from Q1_base
alone, so Q5 must always be asked, regardless of what Q1 or Q4 produced or whether Q4
was skipped.

**No other question qualifies for a skip.** Q2 (routing profile), Q3 (ship/ticketing
variant), Q6 (skill-delivery module), Q7 (stack/ADAPT values), and Q8 (opt-in add-ons)
each bind a flag or module selection that the Q1/Q4/Q5 rigor computation cannot
determine on its own — none of them become moot at any point in this resolution, so
none of them are ever skipped.

---

## Override bounds

A member may override the module set the resolved profiles select — dropping an
offered module, or adding one that wasn't offered. The override is bounded by one
rule, stated in full:

> A per-module override may not drop a module that any installed module's
> README-declared dependencies name. This is validated at `START-HERE.md` step 5
> against the module union. A rejected override must be explained to the member.

This exists because step 7's self-check only verifies the transitive import closure of
shipped Python files — it can never see a dependency a module's README declares in
prose. Example of the class of gap this catches: `27-data-handling`'s README might
state that its rule needs `26-code-discipline` or `24-skill-delivery` present to make
sense; nothing in Python `import` statements would ever reveal that connection.
Checking the override against the module union at step 5 — before any file is
copied — is what catches this class of prose-level wiring that the step-9
import-closure check structurally cannot see.

If a member asks to drop a module that another selected module depends on, refuse the
override, name the specific dependency it would break, and let the member decide
whether to also drop the dependent module (removing both together) or keep the
dependency in place (keeping both).

---

## Writing `install-spec.json`

At Q9's confirmation, write `install-spec.json` at the destination repo root — this file
is `installer.py`'s ENTIRE input (`START-HERE.md` step 6). Its schema:

```json
{
  "kit_version": "<from handoff-kit/VERSION.md>",
  "rigor": "FULL",
  "routing": "PRO",
  "modules": ["00-core", "..."],
  "variants": {"21-pipeline-skills": ["REVIEW/SKILL-full.md", "GIT/SKILL-local.md"]},
  "flags": {"env": "local", "pii": true, "desktop_app": true, "debate": true, "no_code": false},
  "adapt": {
    "PROJECT_NAME": "...", "PROJECT_ONE_LINER": "...",
    "TEST_CMD": "...", "LINT_CMD": "...", "TYPE_CMD": "...",
    "SHARED_CODE_HOME": "...", "TICKETING_VARIANT": "the local `tickets/` folder"
  },
  "overrides": []
}
```

`modules` is the resolved union from step 5 above (not a raw Q1/Q4/Q5 encoding).
`variants` holds ONLY skill-variant choices — the Q3 ticket-template rename is keyed on
`flags.env=="local"`, not a `variants` entry. `TICKETING_VARIANT` in `adapt` is required
iff `25-ticketing` is in `modules`; its value is substituted into inline PROSE
(`modules/25-ticketing/claude-md-block.md`), so it must be the readable phrase — write
exactly `GitHub issues` when `flags.env=="github"`, or exactly ``the local `tickets/`
folder`` when `flags.env=="local"`. Never a bare keyword like `"local"` (a live install
trial produced that and it rendered a garbled CLAUDE.md sentence). `no_code:true` renders the Definition-of-Done's
`TEST_CMD`/`LINT_CMD`/`TYPE_CMD` as the literal string `N/A` (installer.py does not special
-case this — the interview writes `"N/A"` directly into `adapt` for those three keys).
