### Hard rules (00-core)

1. Never assume — confirm with research, analysis, or data; label every load-bearing claim Verified / Estimated / Assumed / Unknown.
2. Always invoke systematic-debugging for bugs, never brainstorming — brainstorming is for features.
3. Before hypothesising about a bug, build a deterministic reproduce/isolate feedback loop first.
4. Never claim "fixed" without confirming in the real environment — not a manual simulation.
5. Verify before declaring complete — run the actual check and read its output, don't assert.
6. After every mistake, log one row (category, mistake, lesson); promote a recurring lesson to a hard rule.
7. Before naming a new ticket ID, confirm it does not collide with an existing one.
8. Communication: lead with the answer then the reasoning; no preamble/filler; cite `file:line` over prose; match the reader's expertise (spell out shorthand on first use); put wide/tabular data in fixed-width code blocks.

Full text + rationale: `docs/harness/00-core.md`.
