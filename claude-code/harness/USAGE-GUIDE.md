# Usage Guide — working with the harness, step by step

This is the doc you keep open **next to** Claude Code once the harness is installed.
`INSTALL-GUIDE.md` got you here; this guide is for every day after. It explains
what the harness actually is, and then walks you through a real piece of work
step by step — what you type, what Claude does, what appears on disk, and
how you know each step is done. Token saving tips sit inside the step where they
apply, so they're at hand right when you need them.

It is written mainly for the **STANDARD** and **FULL** versions. If you have LIGHT,
read sections 1–3 and you're done — LIGHT deliberately has no workflow to walk
through, but section 3 shows how the same skills work as stand-alone everyday
tools, which makes LIGHT a good first taste of harness-style working.

---

## 1. What is this harness?

Without a harness, working with Claude Code is one long improvised conversation:
you describe what you want, Claude starts writing code, and quality depends on
whether anyone remembered to plan, test, and double-check. Sometimes that goes
fine. On anything that matters, "sometimes" is the problem.

The harness turns that conversation into **staged work with checkpoints**:

- Work is split into **phases** (think it through → write it down → build it →
  check it → ship it), and each phase leaves a **file on disk** — a ticket, a spec,
  a plan — so the next phase starts from a written record instead of a fading
  conversation.
- **Hooks** (small scripts that run automatically around Claude's actions) block
  the known failure modes: skipping the plan, shipping without review, claiming
  something is true without a source.
- **Skills** (pre-written instruction sets Claude follows) make the repeatable
  parts — reviewing, shipping, reporting — run the same disciplined way every time,
  instead of however that day's conversation happened to go.

The payoff: fewer surprises, fewer "wait, why did it do that?" moments, and a
paper trail you can audit. The cost: a bit more ceremony per piece of work. The
three versions below are three different settings on that trade-off dial.

---

## 2. Which version do you have?

Open `HARNESS-VERSION.md` at your repo root — the installer wrote your resolved
**rigor profile** (LIGHT / STANDARD / FULL) and **routing profile** (PRO / MAX5 /
MAX20) in there. You don't choose these day to day; the install interview chose
them from what you're building and what Claude plan you're on.

| Version | In one sentence | Who lands here |
|---|---|---|
| **LIGHT** | Just build it and check it once — no tiers, no hooks, no pipeline. | Skills-only deliverables with nothing to break. |
| **STANDARD** | Plan before building, one review after. | Automations and document-heavy workflows — no user-facing app or database of their own. |
| **FULL** | Plan, map the blast radius, review until clean. | Code-heavy projects: a real application, service, or pipeline. |

Two things worth knowing about how you got your version:

- **Code-heavy projects land on FULL automatically.** That's not an upsell — a
  project with real users, real data, or an ongoing maintenance surface earns the
  full checkpoint set by what it can break (`profiles/rigor-FULL.md`).
- **STANDARD is not "the docs-don't-matter tier."** STANDARD projects run
  automations *and* produce important documents — process guides, runbooks,
  policies. Those documents go through the same T2 pipeline as a code feature
  (section 4 explains why).

The **routing profile** is about models, not process: it fixes which Claude model
handles which role (fast/cheap models for lookups, stronger models for review).
On a Pro plan, token discipline is load-bearing — the tips in this guide exist
mostly for you.

---

## 3. The skills the workflow uses

Section 1 said skills are pre-written instruction sets Claude follows. Here are
the ones you'll actually meet, so that when the walkthrough later says "REVIEW
runs" or "Claude writes a plan," you already know what's happening. Two things
up front:

- **The harness chains them for you.** In the walkthrough (section 6) you
  rarely invoke these by name — you say "start the ticket" or "write the plan"
  and the right skill picks up. The names below are so you recognize what's on
  screen.
- **Each one also works on its own.** Outside a ticket, you can ask for any of
  them individually — they're useful as everyday tools, not only as pipeline
  stages.

### From the Superpowers plugin (a STANDARD/FULL install prerequisite)

- **Brainstorming** — turns a rough idea into a **spec**. Claude asks you
  clarifying questions one at a time, looks at the relevant code, lays out
  design options with their trade-offs, and writes the result to disk: what
  will be built and how you'll know it's right (the acceptance criteria).
  Spec writing isn't a separate skill — the spec is what brainstorming
  produces at the end.
- **Plan writing** — turns an approved spec into a **plan**: the work broken
  into small, ordered tasks, each with its own test, written to a plan file.
  The last thinking step before any code gets written.
- **Subagent implementation** — executes the plan by dispatching a fresh
  helper agent per task, instead of doing everything in one ever-growing
  conversation. Each helper reads its own task from the plan file, does the
  work, and reports back — so the main session stays small.
- **Code reviewer** — a fresh pair of eyes: a separate Claude context that
  didn't write the code reads it hunting for problems. The kit's REVIEW skill
  (below) dispatches one for you at the right moment, but you can also ask for
  one directly, any time: *"Dispatch a code reviewer over the changes on this
  branch."*
- **Code explorer** — the side skill worth knowing about. An explorer agent
  reads unfamiliar code and maps it: how a feature actually works, what calls
  what, where things live. It's the strongest first move on a repo or
  subsystem you haven't worked in before — *"Send a code explorer to map how
  authentication works in this repo"* gives you (and Claude) a grounded
  picture before you scope a ticket against code nobody in the session has
  read yet.

### Installed by the kit (which ones you have depends on your version)

- **REVIEW** — the severity-graded review. STANDARD installs the single-pass
  variant; FULL installs the looping variant (section 7). Every finding it
  returns carries a grade:
  - **P0 — blocker.** Something genuinely dangerous: a logic error that
    produces wrong results, a security hole, a risk of corrupting data.
    Shipping is blocked until it's fixed.
  - **P1 — major.** A real problem with contained impact: wrong behavior in an
    edge case, a critical path with no test covering it, code doing something
    the spec didn't say. Also blocks the ship, also must be fixed.
  - **P2 — minor.** Style, naming, a missing docstring, a small cleanup
    opportunity. Never blocks — it's recorded as a `TODO` in the code and
    shipped, to be cleaned up later as small T1 work. P2s are deliberately
    *not* fixed during review: polishing style mid-review spends budget that
    should go to real problems.
- **GIT** — the ship skill. Runs the pre-flight gate (were the phases actually
  done? is the evidence on disk?), then merges/pushes per your configured
  variant (GitHub PR flow, or local merge).
- **MAP** — FULL only. The blast-radius check between spec and plan
  (section 7).
- **REPORT** — FULL only, for T3 tickets. Writes the post-ship record
  (section 7).
- **COUNCIL / DEBATE** — optional add-on, offered at install for any version.
  Multi-perspective debate tools for big design decisions: several
  differently-prompted agents argue a question before you commit to a
  direction. If you didn't pick the add-on, you don't have these.

### If you're on LIGHT

LIGHT installs none of the pipeline skills — but this section is still for
you. The Superpowers plugin isn't *required* at LIGHT, but nothing stops you
from installing it, and every plugin skill above works well on its own:
brainstorm an idea into a written spec, send an explorer into a codebase you
just inherited, ask for a one-off review of something you wrote by hand. Used
that way, LIGHT plus a few individual skills is a gentle introduction to
harness-style working — the full pipeline is these same skills run in
sequence, with checkpoints between them.

---

## 4. Tickets and tiers: T1, T2, T3

Every piece of work starts with one question: **how much damage could this change
do if it goes wrong?** The answer picks a **tier**, and the tier picks how much
process the work gets. Classifying the tier is always the first step of a session —
before any code, before any brainstorming.

- **T1 — small and safe.** A typo, a doc touch-up, a config tweak, a tiny fix with
  no logic change. Almost no process: make the fix, run the safety check and the
  tests, commit, ship. Minutes, not hours.
- **T2 — a normal piece of work.** One well-defined thing with bounded scope — a
  feature, **or an important document**. A doc counts as T2 when getting it wrong
  has consequences: a process guide others will follow, a policy, a runbook, a
  spec. Nothing can break at runtime, but the think-plan-review loop is exactly
  what catches a wrong instruction before ten people follow it. Trivial docs stay
  T1.
- **T3 — high stakes.** Only exists on FULL. For changes that touch money, shared
  data, or several systems at once. Same loop as T2, plus a mandatory
  blast-radius mapping step before planning (section 7), a deeper review loop,
  and a written report after shipping.

STANDARD installs only T1 and T2 — there is deliberately no T3
(`profiles/rigor-STANDARD.md`). If work on a STANDARD install keeps looking
T3-shaped, that's a signal the project has outgrown its version, not a reason to
improvise extra process.

### What "escalation" means

Three different things share this word. Keep them apart:

1. **Escalating the classification — you, at the start.** Unsure whether it's T1
   or T2? Go one tier up. The cost of extra process is small; the cost of skipped
   process on a risky change is not.
2. **Automatic promotion — the harness, during work.** If the changed files turn
   out to touch paths marked risk-sensitive at install time (`RISK_PREFIXES`), the
   harness promotes the ticket to a `-RISK` variant on its own, so a change that
   wanders into risky territory automatically gets the extra care it needs.
3. **Escalating to a human — the harness, when stuck.** Review loops have round
   caps (section 7). If reviews keep finding problems past the cap, or keep
   re-arguing the same point with no new evidence, the harness stops and hands
   the problem back to you — because at that point the *spec* is wrong, and no
   amount of extra reviewing fixes a wrong spec.

---

## 5. Step zero, every time: scope a ticket

Before starting any T2-or-bigger work, spend one short session turning your idea
into a **ticket** — a small file that states what you want, why, what's in scope,
and what's out.

**What you type:**

> Scope a ticket for feature X. Write it to the tickets folder. Don't start any
> implementation — just the ticket.

**What Claude does:** asks you a few clarifying questions, looks at the relevant
part of the codebase, and writes something like `tickets/2026-07-15-feature-x.md`.

**Done when:** the ticket file exists and you've read it and agree with the scope.

**Why this saves tokens (and grief):** the expensive first phase of the pipeline —
brainstorming — starts sharp instead of vague. Claude reads one small file and
already knows the goal, the boundaries, and the no-gos, instead of spending the
first half of an expensive session interrogating you from scratch. It also gives
you a natural place to stop scope creep: if an idea isn't in the ticket, it's a
*new* ticket.

> **Token saving tip — end the scoping session here.** Don't roll from scoping straight
> into brainstorming in the same session. The ticket file carries everything
> forward; the scoping conversation is now dead weight. Start fresh.

---

## 6. The STANDARD walkthrough (T2, step by step)

This is the full life of one T2 ticket on STANDARD. FULL users: read this too —
FULL is this walkthrough plus the additions in section 7.

The one habit that matters throughout: **end each phase, then `/clear` (or open a
new session) before the next one.** Every phase writes its result to disk, so a
fresh session loses nothing — it re-reads a small file instead of dragging a huge
conversation behind it. On a Pro plan this is the single biggest token saver
available to you, and it's the difference between a ticket fitting your usage
window or not.

### Step 1 — Open and classify

**You type:** "Start ticket `tickets/2026-07-15-feature-x.md`. Classify the tier
first."

**Claude does:** reads the ticket, proposes a tier ("This looks like T2 —
confirm?"), and waits.

**Done when:** you've confirmed the tier. If it's T1, you skip to Step 5 — T1 is
just fix → check → test → commit → ship.

### Step 2 — Brainstorm and spec

**You type:** confirmation, plus anything the ticket doesn't capture (taste,
constraints, examples).

**Claude does:** works through the design with you — options, trade-offs, edge
cases — then writes a **spec**: a short document stating what will be built and
how you'll know it's right (the acceptance criteria). The spec lands on disk under
your docs folder.

**Done when:** the spec file exists, you've read it, and the **spec review** has
run — a second, fresh pair of eyes (a separate Claude context that didn't write
the spec) checks it for holes before anything gets built. The harness's ship gate
later verifies this review actually happened, so don't skip it.

> **Token saving tip — this review is your one bullet on Pro.** The Pro routing profile
> budgets exactly one second-opinion review per ticket, and it fires here, at the
> spec gate — the point of maximum leverage, where a caught mistake is a sentence
> to fix instead of a rebuilt feature. Help it land: point the reviewer at the
> spec *file* and say what worries you ("attack the error handling assumptions"),
> rather than pasting the whole conversation.

> **Token saving tip — keep the spec narrow.** Every file the spec touches is a file the
> plan, the implementation, and the review must cover too. "While we're in there,
> also…" is how a cheap ticket becomes an expensive one. New idea → new ticket.

### Step 3 — `/clear`, then plan

**You type:** `/clear`, then: "Write the plan for `<spec file path>`."

**Claude does:** reads the spec fresh and writes a **plan** — the work broken
into small, ordered tasks, each with its own test — to a plan file on disk.

**Done when:** the plan file exists and reads like something a competent stranger
could execute: each task small, concrete, and checkable.

> **Token saving tip — the plan is for pointing at, not pasting.** During
> implementation, tasks get handed to helper agents by *reference* ("read lines
> 40–80 of the plan file"), never by pasting task text into the conversation.
> The harness's dispatch hooks enforce this at both STANDARD and FULL.
> Same principle for you: if you want to know what the
> plan says later, ask Claude to have a cheap helper look it up — don't make the
> main session re-read the whole plan. A good version of that ask names the
> file, the task, and exactly what should come back:
>
> > *"Use a haiku subagent to look up what the plan at
> > `docs/plans/2026-07-15-feature-x-plan.md` says about task 4 — report back
> > just that task's steps and its test, nothing else."*

### Step 4 — `/clear`, then implement

**You type:** `/clear`, then: "Execute the plan at `<plan file path>`."

**Claude does:** first writes a **standing brief** — the context every helper
needs (on STANDARD a single line naming the branch suffices; FULL uses a fuller
one-page version listing the branch, the tier, the acceptance criteria, and a
pointer to the MAP check described in "What FULL adds" below) — then works
through the plan task by task, dispatching helper agents for the actual edits,
running tests as it goes, and committing when they pass. The dispatch hook blocks
helper-agent work until the standing brief exists — if you see that block
message, it's the harness working, not breaking.

**Done when:** every plan task is done, the test suite is green, and the work is
committed on a feature branch.

> **Token saving tip — cheap models for cheap work.** Lookups (find a file, check a git
> log, confirm a test name) belong to the fast, inexpensive model tier, batched
> into one helper call — not run one by one in the main conversation where every
> line costs premium-model prices. The routing profile handles this
> automatically — it works best left alone. A stronger model adds nothing on
> mechanical work like lookups; save the premium tier for the phases that
> genuinely need it (design, review).

### Step 5 — `/clear`, then review

**You type:** `/clear`, then: "Run REVIEW on this branch." The implementation
conversation is usually the longest one of the whole ticket, and the reviewer
doesn't need any of it — the change is on the branch, the spec is on disk.

**Claude does (STANDARD):** dispatches **one** fresh-context reviewer over the
whole change. Findings come back graded — **P0** (must fix — real defect), **P1**
(must fix — wrong behavior or missing critical test), **P2** (minor — logged as a
TODO, doesn't block); section 3 explains the grades in full. Claude fixes the
P0s and P1s.

**Done when:** the single pass is done and its P0/P1 findings are fixed. STANDARD
deliberately runs **one** pass — if the fixes themselves feel risky or the
reviewer found something structural, the right move is to stop and rethink the
spec, not to loop reviews (that looping discipline is what FULL adds).

> **Token saving tip — arrive clean.** A review round costs the same tokens whether it
> finds lint-level noise or real bugs. Run the tests and linters *before*
> invoking REVIEW so the reviewer's attention (and your budget) goes to genuine
> issues.

### Step 6 — Ship

**You type:** invoke the installed ship skill (`GIT`). No `/clear` needed
between review and ship — shipping is the one cheap phase: the gate reads
everything it needs (the branch, the review evidence) from disk, so it can run
in the same session that finished the review.

**Claude does:** runs the pre-flight gate — including the check that the spec
review from Step 2 actually happened — then merges/pushes per your configured
variant (GitHub PR flow, or local merge).

**Done when:** the branch is merged and the gate reported clean. The ticket is
closed. `/clear` before you touch the next one.

### The same walkthrough, for an important document

On STANDARD, a T2 "feature" is often a document — a runbook, a process guide, a
policy. The steps don't change, only their flavor: the spec says what the document
must cover and who must be able to follow it; the plan breaks it into sections;
"tests" become concrete checks ("a new team member can execute section 3 without
asking anyone"); REVIEW reads the document adversarially, hunting for the
instruction that's wrong or ambiguous *before* ten people follow it. Treat wording
findings with the same seriousness as bug findings — for a document, wording *is*
the logic.

---

## 7. What FULL adds

FULL is the STANDARD walkthrough with four additions. If you're on FULL, everything
above still applies.

### MAP — the blast-radius check (between spec and plan)

After the spec is approved and before planning starts, FULL requires a **MAP**
pass: Claude traces the complete chain of effects of the proposed change — every
file, config, and consumer it touches — and adversarially checks the spec's
assumptions against reality. Think of it as asking "what else does this touch,
and does the spec know about it?" *before* the plan bakes in a wrong assumption.

MAP has a **fixed budget**: two rounds plus at most one reopen. It cannot spiral
into an endless investigation — the cost lever isn't the rounds (those are fixed),
it's the size of the surface your spec touches. A narrow spec maps cheaply; a
sprawling one doesn't. One more reason to keep tickets small.

### REVIEW runs as a loop, not a pass

Where STANDARD reviews once, FULL loops: review → fix P0/P1 → **review again** —
because fixes introduce new bugs, and a fix that nobody re-checked is just a new
unreviewed change. The loop exits only when a round comes back with zero P0 and
zero P1. Round caps — 3 for T2, 5 for T3 — are checkpoints, not hard stops: at the
cap, the work either terminates (nothing new found), continues (still finding
real issues), or **escalates** (the same argument keeps repeating — meaning the
spec is wrong, and you, the human, need to revise it).

This loop can't run away from you: a new round happens only because the
previous one found real P0/P1 problems, and each round exists to check the
fixes — not to re-open things already settled. A clean round ends the loop on
the spot, and a finding that comes back a second time with no new evidence
triggers the escalation above instead of another round.

### T3, for the riskiest work

T3 exists only on FULL: money, shared data, multi-system changes. It runs the same
pipeline with the deeper review cap (5 rounds), and adds a **REPORT** after
shipping — a written record of what changed, what was found, and what state the
system is in now. If you're not sure whether something is T2 or T3, it's T3.

### The guards

FULL also installs background guards you'll mostly notice as occasional blocks:
a **citation guard** that stops Claude from ending a turn with an ungrounded
claim about your code or data ("the tests pass" needs a test run to point at),
and consistency checks on handoff documents. When a guard blocks, Claude revises
its own claim — you don't need to do anything. That's the anti-hallucination
stack earning its keep; it reduces and catches, it does not make hallucination
impossible (see `START-HERE.md` §8).

---

## 8. The Pro-plan token checklist

Everything below is already in the steps above — this is the one-page version to
glance at per ticket.

1. **Scope the ticket in its own session.** Then get out.
2. **`/clear` at every phase boundary.** Spec approved → clear. Plan written →
   clear. Implementation done → clear. The files on disk are the memory.
3. **One concern per ticket.** If the plan is ballooning, split the ticket.
4. **Point at files, don't paste them.** Specs, plans, and briefs get referenced
   by path and line range.
5. **Tests and linters before REVIEW.** Never spend a review round on lint.
6. **Spend the one spec-gate review well.** File path + what worries you.
7. **Let cheap models do cheap work.** Don't upgrade mechanical lookups "to be
   safe."
8. **Watch the clock.** Phase boundaries are free stopping points — do the cheap
   thinking phases at the end of a usage window, start the expensive build phase
   on a fresh one.
9. **When review keeps circling, stop.** Escalation is the harness saving your
   budget, not wasting your time. Revise the spec.

---

## 9. When things go sideways

- **A hook blocked something and you don't know why.** Read the block message —
  the kit's hooks name what they want (a missing brief path, an unreviewed spec,
  an ungrounded claim). The fix is almost always "do the named thing," not "find
  a way around the hook."
- **Review found something structural.** Don't patch around it at review time.
  Stop, reopen the spec, fix the design, re-plan. Cheaper than three more review
  rounds arguing with a broken foundation.
- **The same disagreement keeps repeating.** That's oscillation — the harness's
  own signal to stop and escalate to you. More rounds will not produce new
  evidence.
- **The ticket keeps growing.** Freeze scope: finish what the spec promised, file
  the growth as new tickets. A guide, a spec, or a feature that ships beats three
  that are 80% done.
- **Something looks broken in the harness itself.** Don't self-diagnose past what
  you can see — record what happened and report it, the same honesty standard the
  install flow uses.

---

## 10. What the harness can't do

Honesty section, same spirit as `START-HERE.md` §8–9:

- **It can't verify which model actually served a request.** The routing table
  works by *asking*: a dispatch says "use the cheap model for this lookup," and
  Claude Code passes that request along. What nothing in the harness can do is
  check what happened after the ask — if a dispatch names a model your plan
  doesn't offer, the request doesn't fail with an error; the platform quietly
  serves a different model instead, and nothing in the output says which one
  actually ran. So the routing table is a discipline Claude follows, not a
  guarantee the harness can police. The practical consequence: don't hand-edit
  stronger model names into dispatches — on a plan without that model you'd get
  a silent substitute, which is worse than an honest cheaper seat.

  **What FULL adds — detection *after* the fact, not prevention.** On the FULL
  tier the SubagentStop hook reads the model a finished subagent was actually
  *served* (from that subagent's own transcript) and **logs** a warning when it
  falls outside the seat it was dispatched for. This does not close the gap above —
  it is **post-hoc** (the tokens are already spent), **log-only** (it never blocks
  or re-runs anything), and **best-effort** (it can only compare when it can
  recover which seat the dispatch asked for, and quietly skips otherwise). So a
  silent substitution on FULL becomes *visible after the fact* in the logs rather
  than *undetectable* — still not something the harness can prevent up front.
- **Hooks fail open.** A hook that crashes allows the action rather than wedging
  your session. Good for your workflow, but it means a dead hook is a silent
  hole — the post-install smoke test (`INSTALL-GUIDE.md` §3) is what proves hooks
  are alive.
- **It reduces hallucination; it doesn't eliminate it.** The guard stack catches
  a lot, but not everything — keep a healthy skepticism toward claims you
  haven't seen evidence for.
- **It can't make a bad spec build a good feature.** Every gate downstream of the
  spec checks the work *against the spec*. Garbage in, disciplined garbage out —
  the spec review at Step 2 is the gate that matters most, which is why it's the
  one review even the Pro budget always pays for.

---

## See also

- `INSTALL-GUIDE.md` — getting the harness installed and smoke-tested.
- `START-HERE.md` — the normative install flow, plus the honesty statements
  (§6, §8, §9) this guide summarizes.
- `HARNESS-VERSION.md` (in your repo root after install) — which profiles you
  actually have.
- `docs/harness/` (in your repo after install) — the per-module detail docs the
  installed CLAUDE.md points at.
