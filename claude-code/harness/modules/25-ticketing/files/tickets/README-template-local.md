# Tickets

This folder holds one file per ticket. The filename is the ticket ID (for
example, a ticket ID of `FEATURE-WIDGET-01` is the file `FEATURE-WIDGET-01.md`
in this same directory). This is the local-only-folder ticketing variant —
installed instead of GitHub issues because this project answered the setup
interview's Q3 with "local-only folder."

## Before creating a new ticket

Enumerate existing ticket IDs first — check this folder's file listing and
commit history — and choose an ID that does not collide with one already in
use: either the next number in an existing family, or a new prefix that avoids
any ambiguity. This is the project's rule 7 (see `docs/harness/00-core.md`,
"Verify ticket/ID non-collision before naming") applied to this folder
specifically; it is not restated here beyond this pointer.

## Minimal ticket template

Copy this shape into a new file named after the chosen ticket ID:

```
# <TICKET-ID>: <short title>

**Title:** <one-line description of the work>

**Scope:** <what this ticket covers, and what it explicitly does not>

**Status:** <Open | In Progress | Blocked | Done>

**Linked PM report:** <path to the project-update report that covers this
ticket's context, once one exists — leave blank until it does>
```

## Cross-linking with PM reports

When a project-update report documents work tied to this ticket, add its path
to this file's `Linked PM report:` line so the link runs in both directions —
the report references the ticket, and the ticket references the report back.
