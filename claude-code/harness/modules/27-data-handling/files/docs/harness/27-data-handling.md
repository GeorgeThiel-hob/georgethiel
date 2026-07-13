# Harness detail — data handling

Module `27-data-handling` is **kit-authored** — pattern source: a common CLAUDE.md
"Never expose" hard rule (a deny-list of what never leaves the project's boundary),
generalized from secrets specifically to personal/client/financial data broadly.
No other repo source, labeled like module `24-skill-delivery`.

Installs automatically, at ANY resolved rigor profile, when the interview's Q5 ("Will
this project process personal, client, or financial data?") is answered yes — see
`interview/INTERVIEW.md`'s Q5 section. Always co-installed with module
`26-code-discipline`, because Q5 = yes hard-floors the resolved rigor at STANDARD (LIGHT
is removed from the resolution entirely, no override), and STANDARD's module set always
includes `26-code-discipline` — so the "wire the synthetic-data rule into module 26's
tests" branch below is never vacuous, even on a project with no Desktop deliverable.

Four components, matched one-to-one to the spec's four named items for this module:

## (1) Deny-list rules in the installed CLAUDE.md

- Personal, client, or financial data never goes into logs, the lessons-log-equivalent
  file, memory files, commit messages, or any published artifact (a report, a shared
  document, a dashboard).
- Any output that must reference such data minimizes or masks the identifying parts —
  a last-4 digits, a redacted middle section, an initials-only name — rather than
  reproducing it in full.
- Document contents are never sent to an external service (a third-party API, a webhook,
  a paste site) as part of debugging, testing, or demonstrating a feature.

## (2) Synthetic-test-data-only rule

Test inputs must be fabricated or anonymized — never a real client document, a real
account number, a real name paired with real details. This rule wires into whichever
test-verification loop the installed harness actually uses:

- **When module `24-skill-delivery` is installed** (interview Q6 = yes — the deliverable
  is a Desktop-bound skill): the constraint attaches to the fixture-pair convention that
  module defines — `fixtures/<skill-name>/input.md` must contain synthetic or anonymized
  data, never a real client document. The fixture loop's mechanics (build, run, diff,
  iterate) are unchanged; only the *contents* of `input.md` are constrained.
- **Otherwise** (module 24 is not installed — Q6 = no): the constraint attaches to module
  `26-code-discipline`'s test-first tests instead — any test fixture, factory, or sample
  row a test creates or reads must be fabricated or anonymized, never a real client
  document or a real data export.

Module 26 is always present whenever this module is (see above), so this second
branch is always available — it is never the case that Q5 = yes and Q6 = no leaves the
synthetic-data rule with nothing to wire into.

## (3) Desktop-bound skill embedding

A skill delivered for use on the Claude Desktop app carries these data-handling rules
**inside its own instructions**, not only inside the building harness's CLAUDE.md. The
harness's CLAUDE.md governs the session that *builds* the skill; it has no effect on the
session a Desktop user later runs the finished skill in. If the finished skill's own
instructions don't restate "never ask for or retain more personal detail than the task
needs" (or whatever subset of these rules applies to what the skill does), the rule
doesn't travel with the deliverable — the person receiving it isn't protected by any of
the building harness's process. Check this alongside module 24's Desktop
self-containment checklist, when that module is installed.

## (4) Optional WARN-first PII-pattern hook

`files/dot-claude/hooks/lib/pii_pattern_guard.py` — kit-authored, stdlib-only (`re`
plus the same standard library modules used elsewhere in this kit's hooks; no
third-party PII-detection library). Pattern-matches IBAN-shaped, card-number-shaped, and
US-SSN-shaped strings in file content headed for a logs- or memory-shaped destination
path, and — on a match — logs a WARN. It never blocks the write.

**Labeled explicitly: best-effort.** Regex PII detection is imperfect — it catches
strings that are *shaped* like an IBAN, a card number, or an SSN; it does not understand
context, cannot catch a personal detail expressed in prose ("her account, the one ending
in the digits from her birth year"), and will occasionally flag a shaped-but-harmless
string (a false positive) or miss a real one written in an unexpected format (a false
negative). It is a control that reduces exposure and makes some violations visible — it
is not a guarantee that no personal or financial data ever reaches a logged or persisted
file.

See `README.md`'s "Registration" section for how this hook is wired into the installed
`settings.json`.

## Language rule (AC-14)

Every sentence in this module's content — this doc, the README, and the
`claude-md-block.md` digest — uses "reduce exposure" / "make violations visible"
language and does **not guarantee** prevention; the controls above lower risk, they do
not eliminate it.
