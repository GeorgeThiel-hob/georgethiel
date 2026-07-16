# Playbook — Bug Investigation

Record slots in the STANDING BRIEF under `## Playbook slots (bug-investigation)` (lean-mode,
README). Invoke your project's systematic-debugging discipline as usual — this playbook adds
the slots that discipline leaves to judgment. Ladder: see README (all conditions apply
throughout).

## Phase A — before any hypothesis

SLOT:repro-loop — The deterministic, agent-runnable pass/fail signal in the REAL environment
where the bug occurs (exact command or trigger + the failing signal, one line). A hook bug is
triggered via the actual harness, not a bare interpreter snippet; a product bug via the real
product path, not an isolated snippet. If you cannot build one, the specific blocker goes here
and you STOP hypothesising — a deterministic feedback loop that fails fast in the real
environment is the cheapest accelerant available, and skipping it has previously been the
single highest-cost mistake in past investigations (most of a session burned chasing the
wrong root cause while the real cause was visible from the start).
> fill:

SLOT:fresh-state-check — Evidence that the file/DB/config you are reading is CURRENT (main or
the live artifact), not a stale branch copy or old snapshot: `wc -l` + `git log -1
--format=%h -- <file>` on main for files; snapshot date for DBs. Absence-claims from a branch
read are not evidence (a stale file has previously nearly spawned a phantom ticket; a server
file has previously been assumed identical to a merged file when it was not).
> fill:

## Phase B — framings (wrong first framing is consistently the single largest failure class in
## past investigations)

SLOT:framings — MINIMUM 3 candidate framings. For EACH: (a) the mechanism in one sentence; (b)
THE DISTINGUISHING OBSERVATION — something you can check that comes out differently under this
framing vs the others; (c) the cheapest check for that observation. If two framings have no
distinguishing observation between them, you do not yet understand either — read more code
before choosing. Ladder #1 if you pick a framing anyway.
> fill (1):
> fill (2):
> fill (3):

SLOT:framing-verdict — Which framing the distinguishing checks selected, with the decisive
observation quoted (one line) or the [seat:retrieval] checking subagent's report path. "Most plausible" is not
a verdict; a verdict cites the observation that killed the alternatives.
> fill:

## Phase C — before declaring the root cause

SLOT:mechanism-precondition — The chosen framing says "site X fails via mechanism M." Verify
M's preconditions actually hold AT X (file:line of the precondition being met). A mechanism
observed at site A is not evidence about site B (a mechanism observed at one call site has
previously been wrongly generalized to a site with different preconditions, costing multiple
review rounds before being caught).
> fill:

SLOT:temporal-validity — For each load-bearing fact in the diagnosis: PERMANENT (structural,
cite the structure) or SNAPSHOT (time-varying — name the dynamics: what changes it, how fast,
since when). "Never/always/can't" claims get special suspicion (an absolute claim has
previously turned out false because a counter assumed static in fact accrues over time; a
hardcoded path has previously been mistaken for an inherent structural dependency).
> fill:

SLOT:class-sweep — The grep/pattern that enumerates SIBLINGS of this defect across the tree,
and its output. A fixed instance with unswept siblings is an unfixed bug (fixing one instance
and stopping has previously left several identical siblings unfixed, caught only on
re-verification).
> fill:

SLOT:blast-radius — What depends on this diagnosis being right: which conclusions, open
tickets, data repairs, or reports die if the root cause is actually something else. Items here
with high blast radius get the [seat:second_opinion] strongest-seat (ladder #8, pre-ship batch) before you act on
them.
> fill:

## Phase D — after the fix lands

SLOT:env-verification — Evidence the fix works in the REAL environment (the repro-loop from
Phase A now passing — one-line signal or report path), not a simulation. For fail-open
mechanisms: an observation that DISTINGUISHES working from silently-inert — "ran normally" is
consistent with both (a fail-open mechanism has previously appeared to run normally while
being silently inert — that is exactly the failure mode this check exists to catch). If
unverifiable this session, the literal words "committed, needs <X> to confirm" go in your
report.
> fill:

SLOT:prevention — One sentence: what architectural change would have prevented this class?
(a lightweight version of a standing project rule, made a slot). "Nothing architectural —
one-off" is a valid fill.
> fill:
