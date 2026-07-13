---
name: debate
description: >
  Spawn 5+ Claude instances into a shared conversation room where they debate,
  disagree, and converge on solutions. Uses round-robin turns with parallel
  execution within each round. Triggers on "debate", "multi-model debate",
  "agent debate", "spawn a chat room", or /debate. Pass a topic as the
  argument.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Debate

**Opt-in brainstorm booster — never a mandatory pipeline step.** Dispatches 5-10 parallel
agents; one run costs roughly 5-10× a normal brainstorm exchange. Reserve it for a wide
design space or a decision that is expensive to get wrong — not for routine implementation
work.

Spawn 5 Claude Sonnet instances (the recommended FULL/MAX-tier shape — fall back per the
routing profile and the model-availability rule on lower plans) into a shared conversation
room. They debate a problem across 3 rounds using round-robin turns (all agents respond in
parallel each round, see full history). A synthesizer agent (Opus where the plan provides
it, else the routing profile's substitute) then merges the debate into a final answer.

**Why this works:** Same model, slight framing variations = systematically different
failure modes. Surfacing disagreements between instances is more valuable than any single
instance's confident answer. Consensus across independent runs filters hallucinations;
divergences reveal genuine judgment calls.

## Execution

### 1. Parse the request

Extract from the user's message:
- **Topic/problem** to debate
- **Mode:** auto (default) or interactive (`--interactive` flag)
- **Agent count:** default 5, user can override
- **Round count:** default 3, user can override

### 2. Classify the topic and select a persona profile

Before writing anything, read the topic and pick the profile that front-loads the most
relevant perspectives. This is a judgment call — pick the single best fit.

| Profile | When to use | Persona order |
|---------|-------------|---------------|
| `strategy` | Strategic direction, sizing/allocation decisions, expected value, live operating parameters, mechanism design | Domain Strategist → Risk Manager → Quantitative Analyst → Systems Architect → AI & Prompt Engineer |
| `risk` | Failure limits, blast radius, correlated loss, allocation/resource ceilings, stop conditions | Risk Manager → Quantitative Analyst → Domain Strategist → Systems Architect → AI & Prompt Engineer |
| `data` | Data quality, calibration, validation methodology, statistical analysis | Data & Calibration Analyst → Risk Manager → Domain Strategist → Systems Architect → AI & Prompt Engineer |
| `code` | Architecture, module design, type safety, testing, refactoring | Systems Architect → AI & Prompt Engineer → Domain Strategist → Quantitative Analyst → Risk Manager |
| `tooling` | Claude Code skills, agent orchestration, prompt design, automation | AI & Prompt Engineer → Systems Architect → Quantitative Analyst → Domain Strategist → Risk Manager |
| `execution` | Rollout/deployment execution under resource-constrained or contended conditions, outcome-capture tactics, latency-sensitive infra | Execution Strategist → Latency Systems Engineer → Reliability Engineer → Domain Strategist → Risk Manager |
| `mixed` | Balanced — spans multiple domains equally | Domain Strategist → Risk Manager → Quantitative Analyst → Systems Architect → AI & Prompt Engineer |

**Rule:** When the topic has a dominant concern, use that profile. For sizing/strategy
questions use `strategy`. For architecture decisions use `code`. For purely risk/allocation
questions use `risk`. When genuinely mixed, use `mixed`.

### 3. Write the topic to a file

Always write the topic to a timestamped file — never pass it inline as a shell argument.
This prevents shell-escaping issues and creates a durable record.

Path: `.claude/skills/DEBATE/topics/<YYYY-MM-DD>-<short-slug>.txt`

The file should contain:
- The full topic with all context, data, and specific questions
- Enough background that agents can reason without external context
- Concrete numbers where available (e.g. actual outcome rates, cost figures, entry
  conditions)

### 4. Run the orchestration script

```bash
python3 .claude/skills/DEBATE/debate.py \
  --topic-file .claude/skills/DEBATE/topics/<filename>.txt \
  --profile <profile> \
  [--agents N] \
  [--rounds N]
```

**Always run in background** — Debate takes 5–8 minutes (5 agents × 3 rounds parallel
per round + delta annotations + synthesis = ~19 Claude calls). Tell the user the expected
wait time before starting.

Default flags:
- `--rounds 3` — 3 rounds is sufficient for most debates; use 5 only for the highest-stakes
  decisions
- `--agents 5` — all personas; reduce to 3 if the topic is narrow and only 3 perspectives
  add value

### 5. Persona pool

Personas are loaded at runtime from the shared `.claude/skills/personas.json` — edit that
file to add or replace personas for your own domain; no code change is needed. The default
pool ships 12 personas; the profiles above use 5 of them each. Full config format:
`docs/harness/31-debate-tools.md`.

### 6. Output format

Each round prints as it completes:

```
Debate — 5 agents, 3 rounds, profile=strategy
Personas: Domain Strategist, Risk Manager, Quantitative Analyst, Systems Architect, AI & Prompt Engineer
Topic: ...

=== Round 1/3 ===

[Domain Strategist] ...response...

[Risk Manager] ...response...
...

=== Synthesis ===

## Consensus
{What the group agreed on}

## Key Debates
{Where they disagreed and how it resolved}

## Recommendation
{The merged answer}

## Dissents
{Any unresolved disagreements}
```

## When to Use

- **Highest-rigor pipeline — opt-in** (run after COUNCIL when COUNCIL was opted in) to dig deeper
  into findings before creating tickets
- Architecture decisions where multiple perspectives matter
- Strategic discussions (e.g., "should we do X or Y", operating-parameter trade-offs)
- Any problem where debate produces better answers than monologue

## When NOT to Use

- **Routine or bounded-scope work** — Debate is for deep research, not implementation
- Simple factual questions
- Tasks that need tool execution (agents are debate-only)
- When speed matters more than thoroughness
