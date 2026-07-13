# Harness detail — ticketing

New tickets always get a non-colliding ID first — that check is `00-core`'s rule
7 (`docs/harness/00-core.md`, "Verify ticket/ID non-collision before naming"); it
is not repeated here. What differs by project is *where a ticket lives*, decided
once at install time by the interview's Q3 answer. Two variants, never both at
once in a single install.

## (a) The github-issues variant

Selected when Q3 = "GitHub repo."

- A new ticket is `gh issue create` with the ticket ID as (or as a prefix of) the
  issue title.
- Ticket status lives on the issue itself — labels, the open/closed state,
  comments recording progress.
- Cross-linking: a PM report (module `21-pipeline-skills`'s REPORT variant) that
  documents work tied to a ticket references it by issue number
  (`gh issue view <number>`), and — where the REPORT skill's own convention calls for
  it — posts a comment back on the issue linking to the report. The link runs
  both directions: the issue points at the report, the report points at the
  issue.
- Before creating a new issue, run the rule-7 non-collision check against
  `gh issue list` (and commit history, per rule 7) — an issue number alone does
  not protect against a *ticket-ID* collision if the same ID string were reused
  in a title.

## (b) The local `tickets/` folder variant

Selected when Q3 = "local-only folder."

- A bare `tickets/` directory sits at the adopter's repo root — never nested
  under any other prefix. One file per ticket; the filename is the ticket ID
  (for example, a ticket ID of `FEATURE-WIDGET-01` is the file
  `tickets/FEATURE-WIDGET-01.md`).
- Ticket status lives inside the ticket's own file — a `Status:` line, updated
  in place as the ticket moves through its lifecycle.
- Cross-linking: a PM report references a ticket by its file path
  (`tickets/<TICKET-ID>.md`); the ticket file itself carries a `**PM context:**`
  or `**Linked PM report:**` line pointing back at the report, mirroring the
  bidirectional-link convention module `21-pipeline-skills`'s REPORT variant
  describes for the github variant.
- The scaffold at `tickets/README-template.md` (copied into the adopter's repo
  only under this variant) explains the one-file-per-ticket convention and
  carries the minimal per-ticket template — see that file for the exact
  fields.
- Before creating a new ticket file, run the rule-7 non-collision check against
  the existing `tickets/` folder listing (and commit history, per rule 7).

## Why local means a bare `tickets/`, never nested under `docs`

The local variant keeps tickets at the repo root (`tickets/`) — a simple, flat
convention that needs no `docs/` nesting. One file per ticket, one folder to
scan, no extra path segments to remember when creating or looking up a ticket.
