# Module 31 — debate-tools

**Purpose:** opt-in brainstorm boosters — COUNCIL (stochastic multi-agent consensus) and
DEBATE (round-robin multi-model debate). Positioned explicitly as "opt-in brainstorm
boosters, never mandatory pipeline steps" (AC-13's required framing) — never gate a ship on
either having run.

**Offered on ANY plan** (interview Q8) — unlike module `30-reasoning-playbooks`, this module
has no Q2 plan-tier gate; the interview's own Q8 reads the token-cost warning to the member
verbatim before they opt in.

## Dependencies

None required. Both skills are self-contained once this module's `files/` payload is
installed.

## AC-6 delta names (both artifacts are scrubbed/parameterized variants, NOT verbatim)

Domain content was fused into the mechanism in both source skills: `model_chat.py`
hardcoded a persona pool inside the script (domain-specific mechanics, terminology, and third-party names), `SMAC/instructions.md` routed its agent-pool composition
on a narrow domain-specific classifier, and both shelled out to this build's own project-specific
schema-validation module. Four named deltas:

- **(a) Persona pools externalized.** Both skills' persona pools are removed from their own
  files and replaced with a load from one shared, domain-neutral `personas.json` (**new**
  file, not present in either source skill). ADAPT note: edit `personas.json` to add/replace
  personas for your own domain — neither skill's own code needs to change. Merge table +
  full field format: `files/docs/harness/31-debate-tools.md`.
- **(b) Classifier generalized to a high-stakes-topic schema**, Q4-keyed (this
  kit's own high-rigor-tier interview question — money, compliance, or irreversible-action
  exposure). The routing MECHANIC (high-stakes → strongest-seat-anchor pool composition) is
  unchanged; only the field names and the triggering question generalize. Full fields
  table: `files/docs/harness/31-debate-tools.md`.
- **(c) Standalone generalized schema validator shipped** — no dependency on any project's
  own package layout, no `-m`-style package-module invocation anywhere in this module. This
  goes beyond the earlier handoff bundle this kit supersedes, which documented the same
  dependency problem but chose best-effort degradation and called a full port out of scope;
  shipping the validator here is a kit decision beyond that bundle, labeled as such in
  `files/docs/harness/31-debate-tools.md`'s "v1 comparison" section — that bundle's
  degrade-gracefully behavior is kept as the fallback when validation fails (the 3-step
  escalation protocol in both skills still ends in "halt and report to orchestrator", never
  a silent block).
- **(d) Domain prose scrub in `model_chat/SKILL.md`** — the profile table's per-profile "when
  to use" column and the topic-file-contents bullet's worked example both carried
  domain-specific language (a named platform-specific mechanism, a named pair of headline
  outcome metrics); both rewritten to domain-neutral equivalents.

## Token-cost warning (AC-13 — same substantive wording in three places)

1. `README.md` (this file) — see "Purpose" above and the interview cross-reference below.
2. **Each SKILL.md** (`COUNCIL/SKILL.md` and `DEBATE/SKILL.md`) — both open with:
   "dispatches 5-10 parallel agents; one run costs roughly 5-10× a normal brainstorm
   exchange."
3. **The plan-tier interview** — `interview/INTERVIEW.md` Q8 reads this token-cost warning
   to the member verbatim before they opt in: "one run can consume a large share of a Pro
   usage window — reserve for decisions that are expensive to get wrong." (Spec-cited
   location note: the module-31 spec row names `routing-PRO.md` as this warning's third
   home; on this build, Q8 of `interview/INTERVIEW.md` is where the actual sentence lives —
   this README cross-references the location as built, not as originally cited, so a reader
   following the pointer lands on the real text.)

## Carve-out (Global Constraint 6 / AC-11)

The kit's shipped skills are `COUNCIL` and `DEBATE`. The `SMAC` and `model_chat` names that
remain in this module's docs are historical SOURCE-provenance — they name the two
pattern-source skills this module's persona set, classifier, and schemas were derived from.
Those source-provenance names are kit-legitimate and explicitly NOT deny-listed (AC-11's
stated exception). Only the DOMAIN CONTENT fused into the source skills (personas, the
classifier's field names, and other domain-specific terminology) was
scrubbed; see the delta list above.

## What ships here

- `files/dot-claude/skills/COUNCIL/SKILL.md` — scrubbed/parameterized variant. A
  Skill-tool-discoverable skill invocable as `/council` (frontmatter `name: council`),
  standalone and distinct in name from the Superpowers-plugin SMAC skill (no collision).
  Promoted from a manual-Read reference file to a real skill once the rename removed the
  old same-name collision that had forced the reference-file workaround.
- `files/dot-claude/skills/DEBATE/SKILL.md` — scrubbed variant, invocable as `/debate`.
- `files/dot-claude/skills/DEBATE/debate.py` — scrubbed/parameterized variant.
- `files/dot-claude/skills/personas.json` — **NEW**, externalized domain-neutral persona
  pools shared by both skills.
- `files/dot-claude/hooks/lib/schema_validator.py` — **NEW**, standalone generalized
  validator, no project-package dependency.
- `files/docs/harness/31-debate-tools.md` — persona-config format + merge table, classifier
  field-rename table, validator schema definitions in full, v1 comparison.
- `claude-md-block.md` — the compact CLAUDE.md digest for any profile installing this
  module.

None of these are verbatim copies (copy-only invariant, satisfied by authoring the variant
once, here, at cut time — the installer still only copies).
