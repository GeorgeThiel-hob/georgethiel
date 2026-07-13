# Resolution table — fast-path lookup

> Generated from `interview/INTERVIEW.md`'s resolution algorithm — if the two ever
> disagree, `interview/INTERVIEW.md` governs and this table has a bug. This file exists
> so the installing session can resolve rigor + modules from ONE read instead of also
> opening the three `rigor-*.md` profiles and the module `README.md` files (see
> `START-HERE.md`'s orientation read-set). It copies outcomes already derived in
> `interview/INTERVIEW.md`; it does not invent any new ones.

---

## 1. Rigor resolution — the 12-cell hand trace, mirrored

Same 12 rows as `interview/INTERVIEW.md`'s "12-cell hand trace", in the same order,
reading the same algorithm:

```
rigor = min(FULL, (Q5=yes ? max(Q1_base, STANDARD) : Q1_base) + (Q4_fires ? 1 : 0))
```

| # | Q1_base  | Q4 (risk bump) | Q5 (PII) | Resolved rigor | `27-data-handling`? |
|---|----------|----------------|----------|----------------|----------------------|
| 1 | LIGHT    | no             | no       | LIGHT          | no                   |
| 2 | LIGHT    | no             | yes      | STANDARD       | **yes**              |
| 3 | LIGHT    | fires          | no       | STANDARD       | no                   |
| 4 | LIGHT    | fires          | yes      | **FULL** ← pinned cell | **yes**       |
| 5 | STANDARD | no             | no       | STANDARD       | no                   |
| 6 | STANDARD | no             | yes      | STANDARD       | **yes**              |
| 7 | STANDARD | fires          | no       | FULL           | no                   |
| 8 | STANDARD | fires          | yes      | FULL           | **yes**              |
| 9 | FULL     | no             | no       | FULL           | no                   |
| 10| FULL     | no             | yes      | FULL           | **yes**              |
| 11| FULL     | fires          | no       | FULL (saturates) | no                 |
| 12| FULL     | fires          | yes      | FULL (saturates) | **yes**             |

`27-data-handling` (module `27-data-handling`) is Q5's second, independent effect — it
installs at **any** resolved rigor whenever Q5=yes, on top of whatever the rigor column
already selects (`interview/INTERVIEW.md`'s Q5 section, "PII gate, in full"). It is never
a substitute for the rigor floor in the same row — both effects fire together.

---

## 2. Exact module list + key params, per resolved rigor

These three lists mirror `profiles/rigor-LIGHT.md` / `-STANDARD.md` / `-FULL.md` exactly
— same modules, same conditions, same parameters. Pick the ONE row-block matching the
"Resolved rigor" column above; do not open the other two `rigor-*.md` files as well.

### LIGHT

| Module | Condition | Key params |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | Q6 = yes | `verification: fixture-testing-only` |

No hooks module, no tier system, no pipeline skills at LIGHT.

### STANDARD

| Module | Condition | Key params |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | Q6 = yes | `verification: fixture-testing-only` |
| `10-hooks-base` | always | — |
| `20-tier-system` | always | `tier_scope: LITE` (T1/T2 only) |
| `21-pipeline-skills` | always | `pipeline: brainstorm→spec→implement`, `audit_rounds: 1`, `audit_variant: lite`, `ship_variant: <per Q3>`, `map_mandatory: false` |
| `22-second-opinion-seat` | always | blocking phase-evidence gate (same as FULL) |
| `25-ticketing` | always | — |
| `26-code-discipline` | always | — |

`23-guards` is **not** installed at STANDARD.

### FULL

| Module | Condition | Key params |
|---|---|---|
| `00-core` | always | — |
| `24-skill-delivery` | Q6 = yes | `verification: fixture-testing-only` |
| `10-hooks-base` | always | — |
| `20-tier-system` | always | `tier_scope: FULL` (T1/T2/T3) |
| `21-pipeline-skills` | always | `pipeline: brainstorm→spec→implement`, `audit_rounds: 3` (T3 cap 5), `audit_variant: full`, `ship_variant: <per Q3>`, `map_mandatory: true`, `pm_reports: true`, `standing_briefs: true`, `plan_by_reference: true`, `haiku_batching: true`, `context_offload: true` |
| `22-second-opinion-seat` | always | blocking phase-evidence gate (same as STANDARD) |
| `25-ticketing` | always | — |
| `26-code-discipline` | always | — |
| `23-guards` | always (new at FULL) | — |

Module lists only grow going up the rigor ladder — nothing installed at LIGHT or
STANDARD is ever dropped at a higher tier.

---

## 3. Flag-driven additions — apply regardless of rigor (Q5/Q8 conditionals)

These do not depend on which rigor row fired; apply on top of the section-2 list
whenever their own condition holds:

| Trigger | Module / effect | Condition detail |
|---|---|---|
| Q5 = yes | `27-data-handling` | Any resolved rigor, including LIGHT-base rows (see section 1's shaded column). |
| Q6 = yes | `24-skill-delivery` | Already shown as a conditional row in every section-2 list above — repeated here only as a cross-reference, not a second install. |
| Q3 | ship variant + ticketing variant | `env: local` → `GIT/SKILL-local.md` + local `tickets/` folder; `env: github` → `GIT/SKILL-github.md` + GitHub issues. Only meaningful once `21-pipeline-skills` / `25-ticketing` are in the union (STANDARD+). |
| Q8 — reasoning playbooks | `30-reasoning-playbooks` | Offered only when Q2 ∈ {MAX5, MAX20} **and** resolved rigor ≥ STANDARD (its module-22 dependency is absent at LIGHT). Skipped outright at LIGHT even if offered. |
| Q8 — debate tools | `31-debate-tools` | Offered at **any** Q2 and **any** resolved rigor — no gate. |

---

## 4. Authority note

This table is the fast path for step 4–5 of `START-HERE.md`'s install flow. The
rationale for *why* each cell resolves the way it does — the step-by-step algorithm
derivation, the pinned-cell justification, the skip logic for Q4 — lives in
`interview/INTERVIEW.md`'s "Resolution algorithm" section and is not repeated here.
Read this table to get the answer fast; read that section if you need to defend or
re-derive it.
