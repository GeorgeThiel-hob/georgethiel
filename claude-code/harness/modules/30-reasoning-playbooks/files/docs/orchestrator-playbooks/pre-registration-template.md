# Pre-Registration Template — analysis sessions

Write this file BEFORE the first query against real data, commit it, and record the commit
hash in the data-analysis playbook's `SLOT:prereg-pointer`. The hash freezes the CONTENT; the
before-data ORDERING is honor-system (nothing timestamps data contact). Even so it makes "I
looked until I found something" distinguishable from "I tested what I said I'd test" for any
honest reader.

Copy to: `docs/analyses/<date>-<topic>/pre-registration.md`

---

## Pre-registration — <topic>

**Date / session / branch:**
**Question (one sentence):**

**Hypotheses** — numbered, each falsifiable:
- H1:
- H2:

**Metrics + decision thresholds** — declared BEFORE seeing results; include the comparison
baseline (e.g. your baseline/null expectation, not an assumed 50/50 split):
- M1: <metric> — H1 supported if <threshold>, refuted if <threshold>
- M2:

**Population** — exact filter (SQL/predicate), expected N (order of magnitude), window,
regime boundaries inside the window and how handled:

**Known contaminants to exclude** — and the exclusion check for each (unit mismatches,
seed/synthetic rows, young/short-lived columns, duplicate or ghost records, any known
population-specific exclusions):

**Planned queries** — the minimum set, listed. Extra queries during execution are allowed but
each is logged as a deviation in the playbook's `SLOT:prereg-deviations`:
- Q1:
- Q2:

**Stop rule** — what result ends the analysis early (either direction), so "keep digging
until it looks better" is impossible:

**What would falsify the favored hypothesis** — named in advance:

**Consumers** — who/what will use the answer, so the blast radius is known before the number
exists:
