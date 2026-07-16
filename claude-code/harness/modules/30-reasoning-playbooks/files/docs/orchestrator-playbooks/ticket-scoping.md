# Playbook — Ticket Scoping / Fix-scope Writing

Record slots in the STANDING BRIEF under `## Playbook slots (ticket-scoping)` before writing
any ticket file or issue. For fix tickets born from a bug investigation, the verification loop
on the finding runs BEFORE this playbook (standing project rule). Ladder (README) applies.

SLOT:id-collision — Output of the [seat:retrieval] ID-enumeration subagent (history grep + docs listing +
issue tracker) proving the chosen ID is unused, + the final spot-check
`git log --all --grep='<ID>'` (a near-collision between a new ID and an existing one has
previously been caught only by this enumeration step — skipping it risks silently
overwriting history).
> fill:

SLOT:primary-evidence — The problem statement traced to PRIMARY evidence: file:line, query
output, or incident row — not a summary, not a prior session's conclusion, not this session's
memory of it (ladder #2). If the ticket exists because "an analysis found X", link the
dossier AND restate the one primary observation that carries it.
> fill:

SLOT:already-implemented — The grep(s) proving the change does not already exist, run against
CURRENT MAIN (not your branch): `wc -l` + `grep -n '<the thing>'` on the target files (a stale
branch read has previously nearly scoped a ticket to add something that current main already
had).
> fill:

SLOT:live-path-check — Is the code path this ticket touches ALIVE in production — actually
exercised, not just present? Evidence: execution/usage counts from production telemetry, or a
status ledger row if your project keeps one. Work on a dead path ships clean and accomplishes
nothing (a past ticket shipped cleanly onto a path with a lifetime production execution count
of zero). For non-live tickets: "n/a — <why>".
> fill:

SLOT:divergent-shapes — For any NEW module or public interface: 2-3 divergent interface shapes
(signatures, param/return types, error modes) listed BEFORE elaborating one, then the
deletion-test verdict for the chosen one ("deletion → complexity reappears across N callers
(keep)" / "→ vanishes (absorb)") per `docs/harness/26-code-discipline.md` (existing rules, made
slots). For tickets with no new interface: "n/a".
> fill:

SLOT:scope-boundary — Explicit in/out lists, and for every OUT item that a reader might expect
IN: one line on where it lives instead (deferred ticket, existing mechanism, owner decision).
Deferral is a scope decision, not a defect-class verdict — a deferred sub-population needs its
root named before it is labeled a different bug (a deferred item has previously been
mislabeled as a different bug because its root cause wasn't named before deferring).
> fill:

SLOT:acceptance-criteria — `AC-N:`-prefixed, each EVIDENCE-SHAPED: what artifact/command
output proves it (maps AC → code at audit time). An AC a grep cannot check needs the
observation that checks it named. Guard-type ACs need a negative control — show the guard
FAILING when broken, else it is a silent no-op (a guard test without a negative control has
previously turned out to be a silent no-op).
> fill:

SLOT:collisions — Check against: any in-flight epic/roadmap scope file your project keeps,
your durable memory/decisions log's "parked" or "don't propose" items, and in-flight branches
(`git branch -a` + worktrees). Name each adjacent item and why this ticket does not collide or
how it feeds it.
> fill:

SLOT:pm-pairing — Path of the paired milestone/report artifact (standing rule: every
ticket-creating session writes one; ticket carries an up-link, the report lists the ticket as
a down-link).
> fill:

SLOT:blast-radius — If this ticket's premise is wrong, what downstream work is wasted or
corrupted? High blast radius → [seat:second_opinion] strongest-seat (ladder #8, pre-ship batch) on the premise
before creating the ticket.
> fill:
