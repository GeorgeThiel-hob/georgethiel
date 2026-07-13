# Orchestrator Playbooks — reasoning scaffolds for any session shape

**Purpose:** carry high-rigor orchestration reasoning into sessions run by any model,
independent of which model authored the original scaffold. Each playbook targets one
recurring session shape and defines the mandatory checkpoints ("slots") for that shape, so
a weaker orchestrator's missing thought becomes visible instead of silently absent.

**Provenance rule:** the reasoning CONTENT of these files came from careful, dedicated
authorship and should be treated as durable. Mechanical wiring (hooks, checks) may be edited
by any session; a substantive rewrite of slot CONTENT should get the strongest available
review seat before shipping, or be flagged to the project owner if that seat isn't
available.

## How a playbook works (lean-mode delivery)

A weaker orchestrator's missing thought is invisible; an empty template slot is visible.
Each playbook defines the mandatory slots for one recurring session shape. Delivery and
recording are designed for token economy — an earlier design (copying the whole playbook
file's content into every session record) was rejected as too heavy on the token-economy
axis:

- **Record slots INSIDE the existing standing brief** under a `## Playbook slots (<shape>)`
  section when a brief exists (every session at or above the standing-brief tier — see
  module `20-tier-system`). **Brief-free sessions (the lowest tier ships brief-free by
  design) use a minimal fallback stub at
  `docs/superpowers/briefs/<branch-slug>-playbook.md` containing ONLY the slots section(s)**
  — one `## Playbook slots (<shape>)` section per matched shape. The fallback exists because
  the motivating failure class — a small, brief-free session burning most of its budget on a
  wrong framing — is precisely brief-free-shaped; without the stub, the harness misses its
  own archetype. Default remains the brief: one brief-family artifact, not a second one. The
  ship-time WARN check (`playbook_slots.py`) reads BOTH locations when both exist (brief
  section first, then the stub — split slots are all checked). On tier promotion (a
  stub-only branch later gains a standing brief): migrate the stub's slots section into the
  brief and delete the stub. Why a stub file and not an alternative home: a retrospective log
  (written at/after session end) has no during-session, ship-time-detectable record; and
  reusing the branch's own standing-brief filename for a brief-free session would couple
  slot-recording into brief-gate machinery that assumes a brief exists.
- **Do not paste raw evidence into slots.** An EVIDENCE slot fills as ONE line: the verdict +
  a pointer (file:line, query, or a subagent report path). The one slot with multi-part fill
  notation, `framings` (`> fill (1)..(3):`), is a structured multi-part fill by design: it is
  the orchestrator's own reasoning, not retrieval — an off-thread-retrieval rule does not
  apply to it. `framing-verdict` and `blast-radius` are ONE-LINE slots (verdict + pointer)
  even though their content is judgment. Batch the evidence-gathering the same way you would
  batch plan content: ONE subagent per playbook phase returning ALL of that phase's filled
  slot lines (never per-slot dispatches; a trivial single lookup the orchestrator needs
  immediately stays inline).
- **Checklist delivery**: the playbook file is read ONCE per shape at session start (the
  primary channel).
- **Ship-time presence check**: `playbook_slots.py` is a WARN-first, fail-open backstop run
  at ship time that detects which shape(s) a branch matches and confirms each matched
  shape's slots section is present and filled. The full detection heuristic (the key types,
  the union-not-precedence rule, and the analysis-dossier basename exclusion) lives in that
  module's `_detect_shapes` docstring — this file does not duplicate it.

Every slot line starts with the greppable marker `SLOT:` so the WARN-first presence check
can detect unfilled slots at ship time. An empty slot is not a rule violation — it is a
signal to stop and either fill it or write `SLOT-WAIVED: <reason>` (waivers are visible and
reviewable; silent absence is not).

Slots demand EVIDENCE-SHAPED content (a verdict + pointer to a grep, file:line, query, or
named observation) — never prose reassurance. A slot filled with "checked, looks fine" is an
unfilled slot.

**Honest token accounting (unmeasured):** the slot tax is paid on every matching session. The
savings side is a COUNTERFACTUAL — wrong-framing rework avoided — and its frequency is
UNKNOWN without a dedicated measurement effort. "Net token use falls" is a design HYPOTHESIS,
not a proven result; treat it as such until your own project measures it.

## Which playbook

```
Session shape                                   Playbook
----------------------------------------------  ---------------------------
Unexpected behavior / error / test failure      bug-investigation.md
Querying data to produce a number or verdict    data-analysis.md
  (accuracy, cost, or calibration metrics,        (+ pre-registration-template.md FIRST)
  any census)
Creating/scoping a ticket or fix scope          ticket-scoping.md
```

Mixed sessions use more than one (a bug that ends in a ticket = bug-investigation +
ticket-scoping). Sessions that fit no shape (pure docs, config chores) use none.

A fourth shape — auditing a change to core strategy/execution-style logic before it ships —
is deliberately NOT shipped here. See `excluded/README.md` for why, and for a template
showing what a domain-specific gate playbook looks like for a project that has one.

## The escalation ladder (applies in every playbook, checked continuously)

Conditions are mechanical; the route is not negotiable in-session. "strongest-seat" = a
fresh-context subagent on the strongest available reviewing model, with repo (+ data access
where relevant) read access — treat the packet you send it as claims for it to refute, never
conclusions to confirm (a strong model fed a wrong premise will tend to agree with the wrong
premise). While the strongest model is unavailable, the seat degrades to the next-strongest
fresh-context model — never to self-review.

**Seat budget (leanness bound):** ladder routes to the strongest-seat are BATCHED **per
decision point** — items pending at the same point ride one packet. The pattern: **one
framing-decision dispatch per framings-bearing shape in play** (whenever that shape's
framings slot is reached — session start for bug-investigation, mid-derivation for
data-analysis), **plus one shared pre-ship batch** — i.e. N+1, where N = framings-bearing
shapes in play — count N by framings slots, not by shapes: a framings-bearing single shape =
2 (condition #1 at framing time, #8 pre-ship — they cannot share a packet, the framing answer
is needed to proceed); bug-investigation + ticket-scoping = still 2 (N=1 — ticket-scoping has
no framings slot); bug-investigation + data-analysis = 3 (N=2). The escalation trigger is a
REPEAT dispatch for the SAME decision point → owner, never a silent spend. This bounds the
strongest-seat cost per session explicitly.

```
#  Condition (mechanical)                                    Route
-  --------------------------------------------------------  ----------------------
1  Chosen framing has NO listed observation distinguishing    strongest-seat BEFORE
   it from the runner-up framing                              building on it
2  A load-bearing claim's evidence is a prior dossier,         Re-derive from primary
   report, summary, or your own memory of the session         source or label Unknown
                                                                and STOP building on it
3  About to override, waive, or reinterpret a mechanical       OWNER. Always. No
   gate (verification convergence, audit exit, ship check,    in-session exception
   hook block)
4  A verifier/reviewer/subagent return CONTRADICTS your        Name the disagreement
   framing                                                     explicitly in the next
                                                                artifact; never silently
                                                                adopt either side
5  Same disputed node, two rounds, no new evidence              OWNER (oscillation)
6  The claim "feels obvious / surely settled" and is            Treat as HIGHEST risk:
   unverified                                                   verify now or route #1
7  A number you are about to publish changed >20% since a       Re-run its derivation
   prior artifact stated it                                     before publishing
8  A blast-radius slot names high-cost / multi-item             strongest-seat (pre-ship
   downstream impact and the item is still unverified           batch)
```

**Seat dispatch budget:** a ladder route is the highest-leverage generation moment in the
session, so the seat dispatch should carry the highest reasoning budget the dispatch surface
exposes — not just the strongest model. If your dispatch surface exposes a per-call
reasoning-effort parameter, use it for ladder routes; otherwise dispatch normally — never
block a ladder route on an unavailable budget knob.

## Degradation rule

These files are the durable layer. If the strongest reviewing model becomes unavailable:
ladder routes to "strongest-seat" degrade to the next-strongest fresh-context model;
everything else here keeps working unchanged, with one named exception — if a playbook's
REASONING content is found wrong while the strongest model is unavailable, the provenance
rule blocks a rewrite; flag it to the owner instead. Do not delete or dilute slots because the
seat degraded.
