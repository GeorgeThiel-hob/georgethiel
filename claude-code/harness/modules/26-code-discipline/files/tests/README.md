# Leanness ratchet — opt-in activation

This directory ships two **inactive templates**, not a live test:

- `test_leanness_ratchet.py.template`
- `leanness_baseline.json.template` (contents: `[]`)

The `.template` suffix is deliberate: `pytest` does not collect `*.py.template` files, so a
fresh install's test suite is green out-of-box. The ratchet only makes sense evaluated
against **your own repo's** current lint debt — never against the empty placeholder baseline
shipped here, and never against the pattern-source project's own baseline (which doesn't
apply to your code at all). Shipping either of those as a live starting baseline would make
the ratchet fail immediately on any adopter repo that already has C901/SIM/PLR-family
violations (most real codebases do).

## How to opt in

Run these from your project root, once module 26 has been installed (i.e. once this
`tests/` directory exists in your repo with the two `.template` files above):

1. **Activate the files** — rename both templates back to their live names:

   ```
   mv tests/test_leanness_ratchet.py.template tests/test_leanness_ratchet.py
   mv tests/leanness_baseline.json.template tests/leanness_baseline.json
   ```

2. **Generate YOUR OWN baseline** — do this BEFORE the first `pytest` run. This overwrites
   `tests/leanness_baseline.json` with a snapshot of your repo's current C901/SIM/PLR-family
   violation counts (via `ruff`, resolved as described below), scanned over `src/` by default:

   ```
   python3 tests/test_leanness_ratchet.py
   ```

   This is the step that makes the ratchet start green: your existing debt is grandfathered
   into the baseline, so the suite only fails on violations introduced AFTER this point.

3. **Confirm it's green**:

   ```
   pytest tests/test_leanness_ratchet.py
   ```

4. **Keep it tight** — whenever you fix a flagged violation (or deliberately accept a new
   one, e.g. via the REVIEW skill's Step 2b(iii)(b) baseline-bump guard), re-run step 2's
   command to regenerate the baseline so the ratchet reflects current reality.

If your shared/application code doesn't live under `src/`, retarget the scan root first — see
the parent module's `README.md` ADAPT note (`{{SHARED_CODE_HOME}}` / scan-root retargeting)
before generating the baseline.

### Prerequisite: a resolvable `ruff` binary

The ratchet needs `ruff` resolvable via one of, in order: `$RUFF_BIN` (env override),
`.venv/bin/ruff` (POSIX venv), `.venv/Scripts/ruff.exe` (Windows venv), or `shutil.which("ruff")`
(anything on PATH — uv/poetry/conda/system installs). If none resolve, the ratchet fails LOUD
with a `RuntimeError` naming every candidate it tried — it never silently skips. To point it at
a custom location (a non-`.venv` install, a CI-provisioned binary, etc.), set the `RUFF_BIN`
environment variable to the exact path before running `pytest` or regenerating the baseline:

```
RUFF_BIN=/path/to/ruff pytest tests/test_leanness_ratchet.py
```

## Why this is opt-in, not on-by-default

The ratchet is a **relative** guard — it only detects NEW violations relative to a baseline.
A baseline is only meaningful if it was generated from the repo it's guarding. Two wrong
baselines were considered and rejected:

- **The source project's own baseline** — numbers describing a different codebase's lint
  debt. Meaningless (and misleading) for your repo, and the class of bug this activation
  procedure exists to prevent.
- **An empty baseline shipped as live** — technically "generated," but from nothing. On a
  fresh adopter repo with any pre-existing C901/SIM/PLR-family debt, the ratchet would fail
  on the very first `pytest` run, before you ever had a chance to regenerate it yourself.

Shipping both files as `.template` and requiring the explicit rename + regenerate steps above
means the only baseline that is ever live is one generated from your own current code.
