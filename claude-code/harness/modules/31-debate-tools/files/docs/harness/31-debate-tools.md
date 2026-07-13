# Module 31 — debate-tools detail doc

Full reference for the two debate-tools skills' shared persona config and validator
schemas, so an implementer can extend either without re-deriving the shape.

## Persona-config format (`.claude/skills/personas.json`)

One JSON object with a single `"personas"` array; each entry is:

| Field | Type | Meaning |
|---|---|---|
| `key` | string | Stable identifier referenced by both skills' persona-profile/order lists. Never change an existing key without updating every profile that references it. |
| `name` | string | Display name shown in transcripts and reports. |
| `focus` | string | One-line framing directive — what this persona pays attention to and argues from. |

Both `COUNCIL/SKILL.md` and `DEBATE/debate.py` load this same file at
run time (`.claude/skills/personas.json` — one directory up from either skill's own
directory). Add, rename, or remove personas by editing this ONE file; neither skill's own
code needs to change. If you rename or remove a `key` that a profile/order list or the
COUNCIL anchor pair references, update those references in the same edit.

**Default pool (12 personas)** — a deduplicated merge of the two pattern-source skills'
pools (the pattern-source project kept these as two separate, overlapping pools:
model_chat's 10-key pool — a 5-key base plus a 5-key execution-focused sub-pool — and
SMAC's own 10-row persona table). The merge table below records which shared key each
pattern-source role absorbs, by row position rather than by the pattern-source project's
own role titles (several of which were project-specific and are not reproduced here):

| Shared key | model_chat source key(s) | SMAC source row |
|---|---|---|
| `domain_strategist` | `src-a`, `src-b` | SMAC row #1 |
| `execution_strategist` | `src-c`, `src-d`, `src-e` | — |
| `latency_systems_engineer` | `lat` | — |
| `risk_manager` | `risk` | SMAC row #3 |
| `quantitative_analyst` | `quant` | SMAC row #2 |
| `data_calibration_analyst` | — | SMAC row #5 |
| `subject_matter_analyst` | — | SMAC row #4 (a domain-specific subject-matter role, generalized) |
| `systems_architect` | `infra` | SMAC row #6 |
| `reliability_engineer` | — | SMAC row #7 |
| `ai_prompt_engineer` | `ai` | SMAC row #8 |
| `adversarial_thinker` | — | SMAC row #9 |
| `first_principles_reasoner` | — | SMAC row #10 |

Every pattern-source role from both pools maps to exactly one shared key above (10
model_chat keys + 10 SMAC rows → 12 shared keys, with the overlapping roles merged rather
than duplicated). SMAC's fixed high-stakes anchor pair (its rows #3 and #10) maps to
`risk_manager` and `first_principles_reasoner` — unchanged 1:1, so the anchor invariant
carries over exactly.

## Classifier fields

The topic classifier COUNCIL dispatches before agent spawn is keyed to the same
blast-radius question as this kit's own high-rigor-tier interview question (money,
compliance, or irreversible-action exposure), generalized away from any single domain:

| Field | Notes |
|---|---|
| `touches_high_stakes_logic` | Bool. |
| `schema_change` | Bool. |
| `multi_system_coordination` | Bool. |
| `irreversible_action_gated` | Bool. Broadened beyond any single domain — catches any irreversible-action exposure, not just one instance of it. |
| `routing_decision: "high_stakes_t3"` | Enum value. |
| `routing_decision: "low_stakes"` | Enum value. |
| `confidence` | Float. |

The routing MECHANIC composes the pool with the two anchor personas on the stronger
model whenever the topic is high-stakes; field names and the triggering question are
domain-neutral throughout.

## Validator schema definitions (`.claude/hooks/lib/schema_validator.py`)

Three schemas ship in this module's standalone validator's `_SCHEMAS` dict:

```
smac_agent:
  verdict                 str    required
  confidence               float  required
  reasoning                str    required
  unresolved_objections    list[str]  required

debate_topic_classifier:
  touches_high_stakes_logic    bool    required
  schema_change                bool    required
  multi_system_coordination    bool    required
  irreversible_action_gated    bool    required
  routing_decision             enum["high_stakes_t3", "low_stakes"]  required
  confidence                   float   required

model_chat_delta:
  round                    int    required
  agent_id                 str    required
  position_delta           str    optional
  key_new_argument          str    optional
  concession                str    optional
  unresolved_objections     list[str]  required
  framing_shift             bool   required
```

`smac_agent` and `model_chat_delta` are unchanged from the pattern-source project's schemas
(neither had domain-specific field names). `debate_topic_classifier` replaces the
pattern source's `smac_classifier` schema per the fields table above.

To add a new schema (e.g. for a project-specific debate variant), add an entry to the
`_SCHEMAS` dict following the same `{"name", "type", "required"[, "values"]}` field-def
shape — the validation engine (`ValidationResult`, `_validate_field`, `_validate_object`,
`validate`, `_main`) needs no changes for a new schema.

## v1 comparison (spec §9's honesty note)

The earlier handoff bundle this kit supersedes documented the same `src/`-dependency
problem this module solves, but chose best-effort degradation and called a full port of the
validator out of scope. This module goes beyond that: it ships a standalone, generalized
validator with no dependency on any project's own package layout. The earlier bundle's
degrade-gracefully behavior is kept as the fallback here too — every escalation path above
(the 3-step protocol) still degrades to "halt and report to orchestrator" rather than
blocking silently, so a project that never runs this validator's dependencies still gets a
usable (if unenforced) skill.
