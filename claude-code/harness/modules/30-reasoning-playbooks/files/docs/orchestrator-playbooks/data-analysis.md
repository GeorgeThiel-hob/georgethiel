# Playbook — Data / Metric / Calibration Analysis

Record slots in the STANDING BRIEF under `## Playbook slots (data-analysis)` (lean-mode,
README). **Prerequisite:** a pre-registration file per `pre-registration-template.md`,
written BEFORE the first query against real data. No pre-reg → you are exploring, and the
output must be labeled EXPLORATORY, never cited as a result. Ladder (README) applies
throughout. Read your project's analysis-mistakes log and domain glossary, if maintained,
before filling.

## Before the first query

SLOT:prereg-pointer — Path to the pre-registration file + its commit hash (committed BEFORE
data contact; the hash freezes content — the ordering itself is honor-system, see template).
> fill:

SLOT:population — The EXACT population filter (SQL WHERE / code predicate, one line) and the
denominator it produces. Then the silent-slicer check: for every column in the filter, since
WHEN has it been populated? A filter on a young column silently truncates the window (a
filter on a young column has previously cut a dataset by an order of magnitude and inverted
the published result — always check population size before and after each filter). Exclude
any synthetic/seed rows your system generates for testing or dry-runs before counting real
observations.
> fill:

SLOT:regime-segmentation — Which regime boundaries cross your window (parameter-change eras,
config changes, bug-fix dates, strategy pivots) and how you segment. Lumping periods with
materially different underlying behavior into one aggregate has previously produced a
headline number that doesn't describe any actual regime — segment first, aggregate second.
> fill:

SLOT:unit-audit — For every unit-bearing / threshold column touched: the unit actually in it,
verified against your domain glossary or a spot query — NOT inferred from the column name.
Mixed-unit columns (the same column storing two different units under different conditions)
have recurred repeatedly as a silent contamination source.
> fill:

## While deriving numbers

SLOT:join-cardinality — For every join a published number rests on: the join key, and the
COUNT proving matched-rows vs population (1:1, or explained). An unpinned join can match 0
rows and still return a plausible aggregate (a headline delta has previously been computed
and published before discovering the join key matched zero rows).
> fill:

SLOT:independence-check — For every consistency test used as evidence: derive whether the
compared fields are algebraically independent. If one was computed from the other, the test is
a tautology and proves NOTHING (a consistency check has previously "confirmed" a fabricated
headline number because the two fields being compared were algebraically the same quantity by
definition — the test could not have failed). Name the independent source each check reads; if
it is N/A, the claim is UNVERIFIED — say so.
> fill:

SLOT:framings — MINIMUM 3 candidate explanations for the headline result, ALWAYS including
"artifact of my measurement" (selection, survivorship, unit, window) and, for any edge claim,
the "no real effect" null. Each with its distinguishing observation (what would look different
under it) and the check. (A plausible causal story for a bad period has previously died on
round 1 against a simple counter-observation; a separate "edge" in one segment later turned
out to be a selection or sample-weighting artifact, not a real effect.)
> fill (1):
> fill (2):
> fill (3):

## Before publishing

SLOT:confidence-table — Every load-bearing number: value, N, CI where applicable (a Wilson
interval or equivalent for any proportion/rate metric), and a Verified/Estimated/Assumed/
Unknown label with the query or file:line. A number without N and a label does not leave the
session.
> fill:

SLOT:prereg-deviations — Every place the executed analysis deviated from the pre-reg (added
query, changed threshold, narrowed population), each with a one-line reason. An undisclosed
deviation converts the result to EXPLORATORY.
> fill:

SLOT:blast-radius — Who/what consumes this number (a dashboard, a sizing decision, a gate, an
owner decision) and what breaks if it is wrong. High blast radius → strongest-seat (ladder #8,
pre-ship batch) before publication.
> fill:
