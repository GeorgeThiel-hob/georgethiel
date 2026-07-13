---
name: council
description: >
  Stochastic multi-agent consensus — spawn N (default 5) parallel analyst agents with
  distinct personas over identical context, then aggregate into a consensus report
  (mode / divergences / outliers). Opt-in brainstorm booster. Triggers on "council",
  "multi-agent consensus", "poll agents", or /council. Pass a topic as the argument.
allowed-tools: Read, Grep, Glob, Bash, Task, Write, Edit
---

# COUNCIL — Stochastic Multi-Agent Consensus

> **⛔ PERSONA PRE-FLIGHT CHECK**
>
> This skill carries this project's own persona set — a standalone skill, distinct in name
> from the Superpowers plugin's own SMAC skill (no collision). If you see generic personas
> (Domain Expert, Skeptic, Pragmatist, Optimist, Contrarian, Historian, End-User Advocate),
> STOP — you are using the wrong persona pool. The correct personas are the project's own,
> defined in `.claude/skills/personas.json` and summarized in "Persona pool" below.
>
> **Self-check before spawning agents:** Does every Agent prompt contain one of the persona
> keys listed in `.claude/skills/personas.json`? If not, abort and re-read this section.

**Opt-in brainstorm booster — never a mandatory pipeline step.** Dispatches 5-10 parallel
agents; one run costs roughly 5-10× a normal brainstorm exchange. Reserve it for a wide
design space or a decision that is expensive to get wrong.

Spawn N agents (default 5) with identical context and near-identical prompts. Each
independently analyzes and produces a structured response. Aggregate by finding consensus
(mode), divergences (splits), and outliers (unique ideas).

**Why this works:** Exploits stochastic variation in LLM outputs. Like polling 10 experts
instead of asking one. The mode filters out hallucinations and individual biases.
Divergences reveal genuine judgment calls. Outliers surface creative ideas a single run
would miss.

## Model Routing

**Execution model note:** This skill uses conditional model routing based on topic type.
The Haiku/Sonnet/Opus assignments below are the recommended FULL/MAX-tier shape — on a
lower-tier plan (e.g. Pro), fall back per the active routing profile
(`profiles/routing-*.md`) and the model-availability rule (drop one tier rather than
trusting silent substitution).

- **Topic classifier:** Haiku subagent (`model: "haiku"`) classifies the topic before agent spawn
- **Low-stakes agents:** 5x Sonnet (`model: "sonnet"`) — default pool size
- **High-stakes agents:** 3x Sonnet + 2x Opus (the two designated anchor personas get
  `model: "opus"` — see "Persona pool" below) — default 5-agent pool
- **Synthesis:** Opus where the plan provides it (else the routing profile's substitute) —
  regardless of topic type

## Execution

### 1. Parse the request

Extract from the user's message:
- **Question/problem** to analyze
- **N** — number of agents (default 5; user can override, e.g. "poll 10 agents")
- **Output type** — decision, ranking, analysis, brainstorm, yes/no (infer from context)
- **Context files** — any files, code, or data the agents need to read

If the question is ambiguous, ask ONE clarifying question before spawning.

### 2. Gather context

Before spawning agents, read any files or context they'll need. Every agent must receive the SAME context — the only thing that varies is the framing/persona in their prompt.

### 2b. Classify Topic

Before spawning agents, dispatch a Haiku subagent (`model: "haiku"`) to classify the topic. The classifier prompt:

~~~
Classify this topic for COUNCIL agent routing. Return ONLY a JSON object matching this schema:

{
  "touches_high_stakes_logic": bool,
  "schema_change": bool,
  "multi_system_coordination": bool,
  "irreversible_action_gated": bool,
  "routing_decision": "high_stakes_t3" | "low_stakes",
  "confidence": float (0.0-1.0)
}

Topic: {topic}
Context: {context_summary}

Rules:
- Set routing_decision to "high_stakes_t3" if ANY of the first four flags is true
- Set routing_decision to "low_stakes" if ALL four flags are false
~~~

"High-stakes" is keyed to the same blast-radius question your project uses to classify
its highest-rigor tier (money, compliance, or irreversible-action exposure) — `schema_change`
and `multi_system_coordination` are unchanged from a plain "big decision" reading;
`touches_high_stakes_logic` and `irreversible_action_gated` are the two renamed fields (see
`docs/harness/31-debate-tools.md` for the full field-rename table). The routing MECHANIC
mirrors a common pattern: high-stakes routes to the strongest-seat-anchor pool composition
below; this kit's version generalizes the field names and the triggering question to any
domain rather than a single fixed one.

**Validate the classifier output:**
```bash
python3 .claude/hooks/lib/schema_validator.py --schema debate_topic_classifier --input '<classifier_json>'
```

**Routing logic:**
- If `confidence < 0.8` → re-classify with Sonnet (`model: "sonnet"`)
- If `routing_decision == "high_stakes_t3"` → use high-stakes pool composition
- If `routing_decision == "low_stakes"` → use low-stakes pool composition

**If validation fails, follow the 3-step escalation:**
1. Re-prompt Haiku with validation errors
2. Escalate to Sonnet and re-prompt
3. Halt and report to orchestrator

### 3. Spawn N agents in parallel

Launch all N agents in a SINGLE message using multiple Agent tool calls. Each agent gets:
- **Identical context** (the problem, relevant file contents, constraints)
- **Unique framing** selected from the persona pool below
- **Structured output format** (enforced in the prompt)

**Persona pool** (cycle through these; for N > 10, repeat with "Senior" prefix):

Personas are defined once, shared with the `DEBATE` skill, in
`.claude/skills/personas.json` — edit that file to add/replace personas for your own domain;
no change to this skill is needed. The default pool ships 12 personas, clustered into
overlapping groups so consensus is meaningful within each group while covering the full
scope: a domain/strategy cluster, an execution/latency cluster, a
risk/quantitative/calibration cluster, a systems/reliability/tooling cluster, and two
cross-cutting personas (adversarial, first-principles) that bridge every cluster.

**High-stakes anchor pair:** two personas — `risk_manager` and `first_principles_reasoner`
— serve as the fixed cross-tier consensus anchors whenever the pool composition is
high-stakes (see "Agent configuration" below). This is a permanent structural invariant,
independent of which other persona keys a project adds to `personas.json`.

**Agent prompt template:**

```
You are one of N independent analysts evaluating the same problem.
Your role: {persona_name} — {focus_description}

## Problem
{question}

## Context
{context}

## Instructions
Analyze independently. Do NOT hedge or try to represent all views — commit to YOUR perspective.

Respond in EXACTLY this format:

### Verdict
[Your clear, unambiguous answer or recommendation — 1-2 sentences max]

### Confidence
[High / Medium / Low]

### Reasoning
[3-5 bullet points supporting your verdict]

### Risks / Caveats
[1-3 bullet points on what could go wrong with your recommendation]

### Surprise
[One non-obvious insight, if any — otherwise "None"]

---
Additionally, output a JSON object on a new line matching the `smac_agent` schema:
{"verdict": "your verdict", "confidence": 0.87, "reasoning": "your reasoning", "unresolved_objections": ["any objections"]}
Use a float (0.0-1.0) for confidence, not High/Medium/Low.
```

**Agent configuration — conditional by topic type:**

**Low-stakes pool** (`routing_decision == "low_stakes"`):
- All N agents use `model: "sonnet"`
- Cycle through the persona pool as before

**High-stakes pool** (`routing_decision == "high_stakes_t3"`):
- The two anchor personas (`risk_manager`, `first_principles_reasoner`) use `model: "opus"`
- All other personas use `model: "sonnet"`
- The 2 Opus agents serve as cross-tier consensus anchors — this is a permanent structural invariant

**Agent output schema enforcement:**
Each agent must return a JSON object matching the `smac_agent` schema alongside their markdown response:

```json
{"verdict": "str", "confidence": 0.0-1.0, "reasoning": "str", "unresolved_objections": ["str"]}
```

After each agent returns, validate:
```bash
python3 .claude/hooks/lib/schema_validator.py --schema smac_agent --input '<agent_json>'
```

If validation fails, follow the 3-step escalation protocol.

- All agents run in parallel (single message, multiple Agent tool calls)
- Do NOT use `run_in_background` — wait for all results

### 4. Aggregate results

After all agents return, synthesize into a consensus report. Use this structure:

#### 4a. Tally verdicts

Group agent responses by verdict similarity. Identify:
- **Consensus** (mode) — the answer/recommendation that the majority converged on
- **Agreement rate** — X of N agents agree (e.g., "7/10 agents agree")
- **Confidence distribution** — how many said High/Medium/Low

#### 4b. Identify divergences

Where agents split into distinct camps:
- What are the camps?
- What's the core disagreement?
- Which side has stronger reasoning?

#### 4c. Surface outliers

Unique ideas that appeared in only 1-2 agents:
- What's the insight?
- Is it worth exploring further?

#### 4d. Collect surprises

Any non-obvious insights from the "Surprise" field that deserve attention.

### 5. Present the consensus report

**Synthesis uses Opus where the plan provides it** (`model: "opus"`; else the routing
profile's substitute). If the synthesis agent fails to return output or returns an error,
follow the 3-step escalation: re-prompt the same seat, then halt and report to orchestrator
(there is no higher tier to escalate to).

```markdown
## COUNCIL Report — {topic}
**Agents polled:** {N} | **Agreement:** {X}/{N} ({percent}%)

### Consensus
{The majority verdict, stated clearly}

### Confidence
{Overall: High/Medium/Low based on agreement rate + individual confidence}
- High agreement (>70%) + High individual confidence = **High**
- Mixed agreement (40-70%) or mixed confidence = **Medium**
- Low agreement (<40%) or mostly Low confidence = **Low**

### Key Reasoning (from consensus camp)
{Merged bullet points from the majority}

### Divergences
{Where agents disagreed, the camps, and the core tension}

### Outlier Ideas
{Unique insights worth noting — or "None"}

### Surprises
{Non-obvious findings — or "None"}

### Raw Votes
| Agent | Verdict | Confidence |
|-------|---------|------------|
| {persona} | {verdict} | {conf} |
| ... | ... | ... |
```

## When to Use

- **Highest-rigor pipeline — opt-in** (invoke on a named trigger: novel strategy/architecture
  decision, multi-system change, or wide design space needing competing approaches raced)
- Strategic decisions with multiple valid options
- Code architecture choices (which pattern, which library)
- Risk assessment and threat modeling
- Brainstorming where you want breadth + consensus
- Any question where a single agent might hallucinate or be overconfident
- Validating a hypothesis from multiple angles

## When NOT to Use

- **Routine or bounded-scope work** — COUNCIL is for research, not implementation
- Simple factual lookups (just answer directly)
- Tasks with one correct answer (math, syntax)
- Real-time conversational flow (latency matters)
- When the user wants YOUR opinion, not a poll

## Cost Management

- Topic classifier runs on Haiku — cheap pre-routing step
- Low-stakes topics: all agents on Sonnet (~$3/$15 per 1M tokens), default 5-agent pool
- High-stakes topics: 3 Sonnet + 2 Opus anchors (the two designated anchor personas),
  default 5-agent pool — **scale-up (optional):** for the highest-stakes decisions the
  pool can be widened (e.g. 8 Sonnet + 2 Opus anchors at N=10), but this is an explicit
  opt-in, not the default
- Synthesis step runs on Opus where the plan provides it (else the routing profile's
  substitute) — regardless of topic type
- For low-stakes questions, N=5 (the default) is normally sufficient
- For high-stakes decisions, the default 5-agent pool still applies; go up to N=10-15
  only as the documented scale-up option above

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Agents share context leakage | Each agent is a fresh subagent — no shared state by design |
| All agents give same answer | Good — that's strong consensus. Report it as high confidence |
| Synthesis averages away disagreement | Never average. Report divergences explicitly |
| Skipping outlier analysis | Outliers are the point — they surface what one agent would miss |
| Using too many agents for simple questions | Match N to stakes: 3-5 for moderate, 7-10 for high, 10+ for critical |

## 3-Step Escalation Protocol

When a subagent's output fails schema validation:

1. **Re-prompt same model** — append validation errors to the prompt, ask for corrected output
2. **Escalate one tier** — if second attempt fails, upgrade model (Haiku→Sonnet, Sonnet→Opus) and re-prompt
3. **Halt** — if third attempt fails, stop and report to orchestrator with full error context

This applies to: topic classifier output, agent structured output, and synthesis output.
