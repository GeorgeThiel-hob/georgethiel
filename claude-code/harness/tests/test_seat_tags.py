import re
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]
_ANY = re.compile(r"\[seat:[^\]]*\]", re.IGNORECASE)
_STRICT = re.compile(r"\[seat:\s*([a-z_ -]+?)\s*\]", re.IGNORECASE)
_PLACEHOLDERS = {"[seat:...]", "[seat:<name>]"}
STATIC_SEVEN = {
    "orchestrator",
    "retrieval",
    "workers",
    "audit_reviewer",
    "second_opinion",
    "scaled_reviewer",
    "persona",
}
DUPLICATED_TAG_FAMILIES = {
    "modules/30-reasoning-playbooks": {"second_opinion", "retrieval"},
    "module-22-dual-fallback": {"second_opinion"},
    "per-task-review-pair": {"scaled_reviewer"},
}


def _norm(name):
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _md_files():
    files = []
    for root in (KIT_ROOT / "modules", KIT_ROOT / "profiles"):
        files.extend(root.rglob("*.md"))
    files.extend(KIT_ROOT.glob("*.md"))
    return [f for f in files if "tests" not in f.relative_to(KIT_ROOT).parts]


def test_every_seat_tag_wellformed():
    for f in _md_files():
        for occ in _ANY.finditer(f.read_text(encoding="utf-8")):
            raw = occ.group(0)
            if raw in _PLACEHOLDERS:
                continue
            m = _STRICT.fullmatch(raw)
            assert m is not None, f"malformed seat tag {raw!r} in {f}"
            assert _norm(m.group(1)) in STATIC_SEVEN, f"unknown seat {raw!r} in {f}"


def _seats_under(rel_glob):
    out = []
    for f in KIT_ROOT.glob(rel_glob):
        for occ in _STRICT.finditer(f.read_text(encoding="utf-8")):
            out.append(_norm(occ.group(1)))
    return out


def test_family_module_30():
    for seat in _seats_under("modules/30-reasoning-playbooks/**/*.md"):
        assert seat in DUPLICATED_TAG_FAMILIES["modules/30-reasoning-playbooks"], seat


def test_family_module_22_dual_fallback():
    for rel in (
        "modules/22-second-opinion-seat/claude-md-block.md",
        "modules/22-second-opinion-seat/files/docs/harness/22-second-opinion-seat.md",
    ):
        for occ in _STRICT.finditer((KIT_ROOT / rel).read_text(encoding="utf-8")):
            assert _norm(occ.group(1)) == "second_opinion", rel


def test_family_per_task_review_pair():
    for rel in (
        "modules/21-pipeline-skills/claude-md-block.md",
        "modules/00-core/workflow-table-FULL.md",
    ):
        for occ in _STRICT.finditer((KIT_ROOT / rel).read_text(encoding="utf-8")):
            assert _norm(occ.group(1)) == "scaled_reviewer", rel
