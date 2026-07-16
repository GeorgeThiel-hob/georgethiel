**Kit version:** 1.1.0

**Cut:** manual snapshot (internal source commit not published)

Manual re-cut only; the kit is a snapshot and does not auto-sync with the project it was cut from (spec §10).

## Changelog

- 1.1.0 — KIT-SEAT-ENFORCE-01: hook-enforced seat→model routing (installer seat-table.json emission, PreToolUse seat check, SubagentStop delivered-model detection, seat tags across skill text).

## Cut tooling

`FILE-MANIFEST.json` exists for kit transport integrity (AC-10) — it is a hash manifest
of every file shipped inside `handoff-kit/`, used to confirm the kit arrived at an
adopter's repo unmodified in transit. It is **not** the install update baseline; that role
belongs to `HARNESS-VERSION.md`'s post-ADAPT hash set (AC-15), which is written into the
adopter's repo at install time and tracks drift after local ADAPT edits.

`FILE-MANIFEST.json` carries a SHA-256 entry for every file shipped inside `handoff-kit/`
(build-artifact caches excluded). It is the source of truth for kit transport integrity and
is verified by `tests/test_kit_integrity.py::test_file_manifest_integrity`. **Regenerate it
after any change to a tracked kit file** by running (from the repo root):

```bash
python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path("handoff-kit")
# Skip the manifest itself and every build-artifact cache dir — otherwise a
# stray .mypy_cache / .pytest_cache from a local test run balloons the manifest.
_ARTIFACT_DIRS = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
manifest = {}
for p in sorted(root.rglob("*")):
    if p.is_file() and p.name != "FILE-MANIFEST.json" and not _ARTIFACT_DIRS & set(p.parts):
        manifest[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
(root / "FILE-MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
PY
```
