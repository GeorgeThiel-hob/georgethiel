# Routing profile: PRO

Selected when the interview's Q2 ("Which Claude plan is this account on? Pro / Max 5x /
Max 20x") resolves to **Pro**. `START-HERE.md` step 5 reads exactly one routing profile,
alongside one rigor manifest, to compute the module union and the per-seat model
assignments; this is the file it reads when Q2 resolves here. This profile pairs with any
rigor level (LIGHT/STANDARD/FULL) — routing and rigor are the two independent axes the
step-5 resolution composes, not tiers of each other.

## Seat table

The seat table below is one spec table across three columns, reproduced identically in
all three routing manifests; this file bolds its own column (**PRO**).

| Seat | **PRO (flagship)** | MAX-5X | MAX-20X |
|---|---|---|---|
| Orchestrator | **Sonnet** | Sonnet | Opus 4.8 (or Sonnet for economy) |
| Retrieval | **Haiku** | Haiku | Haiku |
| Workers (code/plan/test) | **Sonnet** | Sonnet | Sonnet |
| Audit reviewer | **Sonnet, fresh context** | Opus | Opus |
| Second-opinion seat | **Sonnet, fresh context; ONE call at the spec gate only** | Opus at spec + audit gates | Opus at every gate (the stronger second-opinion model if the account exposes it) |

## The second-opinion seat is a capability, not a platform guarantee

An `advisor()`-shaped tool is an environment capability, not a platform guarantee: some
accounts and sessions have it, some don't, and no seat assignment above can force it into
existence. The kit defines the second-opinion seat as "the advisor tool if present, else a
fresh-context subagent on the strongest affordable model." The load-bearing property is
**fresh context** — a reviewer that did not produce the work under review — not model
tier. Model tier is a multiplier on top of that property, never a substitute for it.

## Sentinel gate-count for this profile

Module 22's sentinel-evidence gate takes its **required-phase-gate count** from the active
routing profile, not from a fixed constant. This number is a COUNT of distinct phase-gates
that each need their own evidence (spec, audit, plan) — it is never passed as the
`--threshold` argument to any single `--check-phase` call; every phase is checked at
`--threshold 1` (one review is one piece of evidence for that phase). For **PRO**:
`{T2: 1, T3: 1}` — one required phase-gate (spec) at both tiers. Rationale: the ship check
verifies the one spec-gate review happened — it catches "skipped review entirely," the
realistic Pro failure mode.

**Sentinel enforcement strength.** When an advisor tool is present, the gate-evidence
check (the sentinel module) is **gate-grade**: it is forge-resistant and
transcript-visible, so the evidence of a gate having run cannot be fabricated. When the
same role is filled by a subagent seat instead, the check is a **WARN-grade convention**
that the orchestrator could forge. The kit says this plainly rather than claiming
gate-grade enforcement in a configuration that only supports a convention.

## Pro-first rules

PRO is the flagship-constrained profile: fewer, cheaper seats and a tighter usage window
than MAX5/MAX20, so the kit's token-economy discipline is load-bearing here rather than
optional overhead.

- **Token-economy modules are mandatory, not optional, on PRO.** They exist to make rigor
  affordable at this seat budget — disabling them on PRO reintroduces the token cost they
  were built to remove, at the plan tier least able to absorb it.
- **Single-phase sessions with `/clear` at phase boundaries.** Reset context at each phase
  boundary (spec approval, plan approval, audit-clean) rather than carrying one long
  session through the whole ticket.
- **Batched retrieval.** Retrieval-tier lookups (file search, grep, git reads) go through
  a single batched dispatch rather than repeated inline calls.
- **Second-opinion budget = 1 call/ticket, at the spec gate only.** This matches the seat
  table above: PRO's second-opinion seat fires once, at spec approval, not at every gate.

PRO's gate strength comes from context independence, not model tier.

## Model-availability honesty rule

There is no model-list enumeration surface: no API or command lists which model seats
this account may actually dispatch. A dispatch that requests a blocked model does not
error — it silently falls back to the inherited or default model; the CLI surfaces a
substitution notice a human can see, but no agent-side model-availability detection
exists, and this kit claims none. Therefore the seat table above is **authoritative at
install** for this profile. If the member's plan or organization restricts a seat's model,
tell them to drop the routing profile one tier rather than trusting silent substitution.
Never block the install on an availability doubt — install per the table and note the
substitution caveat in the report.
