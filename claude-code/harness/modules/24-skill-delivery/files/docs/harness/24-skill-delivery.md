# Harness detail — skill delivery for Claude Desktop

This module is authored fresh — NO proven source in the pattern-source project. Everything below is
new content written for this kit, not a scrubbed or verbatim copy of anything that
existed before. Two things live here: the fixture-testing loop every Desktop-bound
skill goes through before it ships, and the self-containment checklist that keeps
its instructions usable on the surface that will actually run them.

## (a) The fixture-testing loop

This is the Desktop-skill equivalent of module `26-code-discipline`'s test-first
requirement, for exactly the case where pytest, hooks, or any other Claude-Code-only
verification tool aren't available to the delivered artifact — because the artifact
never runs inside Claude Code once it ships. A Desktop skill only proves itself by
what it produces from a given input, so that is what gets tested.

**The loop, for every skill being built for Desktop delivery:**

1. Author a fixture pair: `fixtures/<skill-name>/input.md` (a realistic sample
   input the skill will actually be asked to process) and
   `fixtures/<skill-name>/expected-output.md` (the output that input should
   produce, written by hand before the skill is run — not derived from a first
   run and then accepted).
2. Run the skill against `input.md`.
3. Diff the actual output against `expected-output.md`.
4. If they don't match, revise the skill's instructions (never loosen
   `expected-output.md` to fit whatever the skill happened to produce) and repeat
   from step 2.
5. Stop only when actual output matches expected output. That match is the
   evidence the skill works — there is no pytest run, no hook, no CI job standing
   behind a Desktop-delivered skill the way there is for repo code.

**Fixture-pair interface (for other modules to build on):** the pair's path shape —
`fixtures/<skill-name>/input.md` + `fixtures/<skill-name>/expected-output.md` — is
the stable contract. A module that needs to attach an additional constraint to a
Desktop skill's test data (for example: "this sample input must be fabricated or
anonymized, never a real client document") constrains the *contents* of
`fixtures/<skill-name>/input.md`, not the loop's mechanics. The loop itself — build,
run, diff, iterate — never changes shape based on what else is installed.

## (b) The Desktop self-containment checklist

A delivered skill's own instructions may reference ONLY what the Claude Desktop
surface actually offers to the person running it:

- File uploads the person attaches to the conversation.
- The conversation itself (what has been said so far, in-context reasoning).
- Artifacts (a rendered document/page the skill produces as output).

A delivered skill's instructions may **NOT** reference:

- Repo file paths (`docs/...`, `src/...`, or any path that only resolves inside the
  building harness's checkout).
- Hook behavior (a WARN or BLOCK gate, a dispatcher, anything that only fires
  inside a Claude Code session with this kit's hooks installed).
- Subagent dispatch (`Agent(...)` calls, named subagent types, multi-agent
  routing) — Desktop has no equivalent concept.
- Anything else that exists only inside the BUILDING harness's Claude Code
  session and has no counterpart on the Desktop surface.

**Why the boundary sits exactly here:** the check applies to the DELIVERED
artifact, not the build harness — the skill being shipped may only use what
Desktop offers (uploads, conversation, artifacts — no repo tools, hooks,
subagents), while the FULL/STANDARD harness building it uses everything it has.
While authoring the skill, the builder's own Claude Code session can read the
repo, trip hooks, and dispatch subagents freely — none of that is restricted, and
none of it is what this checklist is about. The checklist is a pre-delivery gate
on the *instructions the skill itself carries*, checked once the skill is
considered done and before it is handed to a Desktop user, because that is the
only version of the skill a Desktop user will ever actually run.

**Checklist to run before delivery, for every Desktop-bound skill:**

- [ ] Read every instruction line the skill contains. For each one, ask: "would
  this line make sense to someone running it on Desktop, with only uploads,
  conversation, and artifacts available?"
- [ ] Flag any reference to a file path outside an upload, any reference to a
  hook or gate, and any reference to dispatching another agent.
- [ ] Rewrite flagged lines so the same intent is expressed using only the three
  Desktop-available capabilities, or drop the instruction if it has no Desktop
  equivalent.
- [ ] Re-run the fixture loop above after any rewrite — a self-containment fix
  can change behavior, so it needs the same input → output verification as any
  other change to the skill's instructions.
