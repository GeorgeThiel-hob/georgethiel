"""handoff-kit/tests/test_kit_integrity.py — drift detectors for two kit-internal
documents that have no other structural enforcement.

1. FILE-MANIFEST.json (transport integrity, AC-10) is a flat
   ``{relative_path: sha256_hex}`` map — confirmed by reading the file directly,
   not assumed — and every entry must still match the on-disk bytes it names.
2. profiles/resolution-table.md's per-tier module lists (§2) are a hand-mirrored
   fast path over profiles/rigor-{LIGHT,STANDARD,FULL}.md and
   interview/INTERVIEW.md's Qn gates (see resolution-table.md's own "Authority
   note"). Nothing recomputes the table from its sources, so a future edit to one
   side alone would silently drift; this test compares parsed content across both
   sides instead of merely asserting the files exist.

See AC-8 of the kit's hardening design spec.
"""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

KIT_ROOT = Path(__file__).resolve().parents[1]

_MODULE_ROW_RE = re.compile(r"^\|\s*`([A-Za-z0-9_-]+)`\s*\|")
_GATE_RE = re.compile(r"\bQ(\d+)\b")
_MODULE_ID_RE = re.compile(r"`(\d\d-[a-z-]+)`")


def _table_module_ids(block: str) -> list:
    """Return the module ids (e.g. '00-core') named in the first column of every
    markdown table row in `block` — rows shaped '| `<id>` | ... | ... |'. Table
    separator rows ('|---|---|---|') and prose lines never match, so they are
    skipped automatically."""
    ids = []
    for line in block.splitlines():
        m = _MODULE_ROW_RE.match(line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def _section(text: str, start_marker: str, end_marker: str) -> str:
    """Slice `text` from `start_marker` (inclusive) up to the next occurrence of
    `end_marker` strictly after it. Raises ValueError via str.index if either
    marker is missing — a missing marker means the file's structure moved out
    from under this test, which should fail loudly rather than silently parse
    zero rows."""
    start = text.index(start_marker)
    end = text.index(end_marker, start + len(start_marker))
    return text[start:end]


class TestFileManifestIntegrity(unittest.TestCase):
    """AC-8, drift test 1: every FILE-MANIFEST.json entry's recorded sha256 must
    equal the current on-disk bytes of the file it names, and every named path
    must exist."""

    def test_file_manifest_integrity(self):
        manifest_path = KIT_ROOT / "FILE-MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIsInstance(manifest, dict, "FILE-MANIFEST.json is not a flat map")
        self.assertGreater(len(manifest), 0, "FILE-MANIFEST.json is empty")

        for rel_path, expected_sha256 in manifest.items():
            with self.subTest(path=rel_path):
                target = KIT_ROOT / rel_path
                self.assertTrue(
                    target.is_file(),
                    f"FILE-MANIFEST.json names {rel_path!r} but it does not "
                    "exist on disk",
                )
                actual_sha256 = hashlib.sha256(target.read_bytes()).hexdigest()
                self.assertEqual(
                    actual_sha256,
                    expected_sha256,
                    f"{rel_path}: on-disk sha256 {actual_sha256} != "
                    f"FILE-MANIFEST.json's recorded {expected_sha256}",
                )


class TestResolutionTableMatchesProfiles(unittest.TestCase):
    """AC-8, drift test 2: cross-checks profiles/resolution-table.md against its
    two declared sources of truth."""

    @classmethod
    def setUpClass(cls):
        cls.resolution_text = (KIT_ROOT / "profiles" / "resolution-table.md").read_text(
            encoding="utf-8"
        )
        cls.interview_text = (KIT_ROOT / "interview" / "INTERVIEW.md").read_text(
            encoding="utf-8"
        )
        cls.rigor_texts = {
            tier: (KIT_ROOT / "profiles" / f"rigor-{tier}.md").read_text(
                encoding="utf-8"
            )
            for tier in ("LIGHT", "STANDARD", "FULL")
        }

    def _resolution_table_modules(self, tier: str) -> list:
        # Section 2 lists LIGHT, then STANDARD, then FULL, then section 3 begins.
        markers = {
            "LIGHT": ("### LIGHT", "### STANDARD"),
            "STANDARD": ("### STANDARD", "### FULL"),
            "FULL": ("### FULL", "## 3."),
        }
        start, end = markers[tier]
        return _table_module_ids(_section(self.resolution_text, start, end))

    def _rigor_profile_modules(self, tier: str) -> list:
        block = _section(self.rigor_texts[tier], "## Module set", "\n## ")
        return _table_module_ids(block)

    def test_resolution_table_matches_profiles(self):
        # 1. Per-tier module list agreement: resolution-table.md §2 vs. each
        #    rigor-{LIGHT,STANDARD,FULL}.md's own "## Module set" table.
        for tier in ("LIGHT", "STANDARD", "FULL"):
            with self.subTest(check="module-list", tier=tier):
                table_modules = set(self._resolution_table_modules(tier))
                profile_modules = set(self._rigor_profile_modules(tier))
                self.assertGreater(
                    len(table_modules),
                    0,
                    f"{tier}: parsed zero modules from resolution-table.md — "
                    "the table format moved and this parser needs updating",
                )
                self.assertEqual(
                    table_modules,
                    profile_modules,
                    f"{tier}: resolution-table.md's modules "
                    f"{sorted(table_modules)} != rigor-{tier}.md's modules "
                    f"{sorted(profile_modules)}",
                )

        # 2. Every Qn gate resolution-table.md references (Q1_base's underscore
        #    suffix is intentionally excluded by the \b boundary — it names a
        #    derived variable, not a standalone gate reference) must resolve to
        #    an actual "## Qn" heading in interview/INTERVIEW.md.
        gate_numbers = sorted({int(n) for n in _GATE_RE.findall(self.resolution_text)})
        self.assertGreater(
            len(gate_numbers),
            0,
            "resolution-table.md references no Qn gates — parser drifted",
        )
        for n in gate_numbers:
            with self.subTest(check="gate-name", gate=f"Q{n}"):
                self.assertIn(
                    f"## Q{n}",
                    self.interview_text,
                    f"resolution-table.md references Q{n} but "
                    f"interview/INTERVIEW.md has no '## Q{n}' heading",
                )

        # 3. Every module id resolution-table.md names anywhere (§2's per-tier
        #    tables plus §3's flag-driven additions, e.g. `30-reasoning-playbooks`)
        #    must resolve to a real modules/<id>/ directory.
        module_ids = set(_MODULE_ID_RE.findall(self.resolution_text))
        self.assertGreater(
            len(module_ids),
            0,
            "resolution-table.md names no module ids — parser drifted",
        )
        for module_id in sorted(module_ids):
            with self.subTest(check="module-exists", module=module_id):
                self.assertTrue(
                    (KIT_ROOT / "modules" / module_id).is_dir(),
                    f"resolution-table.md names module {module_id!r} but "
                    f"modules/{module_id}/ does not exist",
                )


if __name__ == "__main__":
    unittest.main()
