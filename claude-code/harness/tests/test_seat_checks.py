import importlib.util
import json
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[1]
_LIB = (
    KIT_ROOT / "modules" / "20-tier-system" / "files" / "dot-claude" / "hooks" / "lib"
)
# `seat_checks.py` (module 20-tier-system) does `from . import HookResult`,
# whose definition lives in module 10-hooks-base's lib/__init__.py. At install
# time installer.copy_payload merges every module's dot-claude tree into ONE
# `.claude/hooks/lib/`, so both files coexist. In the unmerged repo they sit in
# separate module dirs, and Python cannot union a regular package (one with an
# __init__.py) across two directories. So we reconstruct the merged `lib`
# package here: load its __init__ from 10-hooks-base and span __path__ over both
# module lib dirs, exactly reproducing the installed layout.
_BASE_LIB = (
    KIT_ROOT / "modules" / "10-hooks-base" / "files" / "dot-claude" / "hooks" / "lib"
)
_spec = importlib.util.spec_from_file_location(
    "lib",
    _BASE_LIB / "__init__.py",
    submodule_search_locations=[str(_BASE_LIB), str(_LIB)],
)
_lib = importlib.util.module_from_spec(_spec)
sys.modules["lib"] = _lib
_spec.loader.exec_module(_lib)
from lib import HookResult, seat_checks  # noqa: E402


def _load_dispatcher():
    """Load a FRESH pretooluse_dispatcher module (its own `_CHECKS` registry).

    Fresh per call so a test's monkeypatch.setitem on `mod._CHECKS` cannot leak
    into another test. `sys.modules["lib"]` is already reconstructed at import
    time (top of file), so the dispatcher's `_maybe_register` imports resolve.
    """
    disp_path = (
        KIT_ROOT
        / "modules"
        / "10-hooks-base"
        / "files"
        / "dot-claude"
        / "hooks"
        / "pretooluse_dispatcher.py"
    )
    spec = importlib.util.spec_from_file_location("pretooluse_dispatcher", disp_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def seat_table(tmp_path, monkeypatch):
    state = tmp_path / ".claude" / "state"
    state.mkdir(parents=True)
    (state / "seat-table.json").write_text(
        json.dumps(
            {
                "routing_profile": "MAX5",
                "generated_by": "test",
                "seats": {
                    "orchestrator": ["sonnet"],
                    "retrieval": ["haiku"],
                    "workers": ["sonnet"],
                    "audit_reviewer": ["opus"],
                    "second_opinion": ["opus"],
                    "scaled_reviewer": ["opus", "sonnet"],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(seat_checks, "_SEAT_TABLE_PATH", state / "seat-table.json")
    monkeypatch.setattr(seat_checks, "_WARN_MARKER", state / ".seat-table-warn-emitted")
    monkeypatch.delenv("SEAT_ROUTING_MODE", raising=False)
    return state


def _disp(model=None, prompt="", description=""):
    ti = {"prompt": prompt, "description": description}
    if model is not None:
        ti["model"] = model
    return {"tool_name": "Agent", "tool_input": ti}


def test_no_model_blocks(seat_table):
    r = seat_checks.check_seat_routing(_disp(prompt="[seat:retrieval] go"))
    assert r.allow is False and "model" in r.block_message


def test_no_tag_blocks(seat_table):
    r = seat_checks.check_seat_routing(_disp(model="haiku", prompt="just do it"))
    assert r.allow is False and "seat" in r.block_message.lower()


def test_unknown_seat_blocks(seat_table):
    r = seat_checks.check_seat_routing(_disp(model="haiku", prompt="[seat:bogus] x"))
    assert r.allow is False and "bogus" in r.block_message


def test_persona_hint_names_module(seat_table):
    r = seat_checks.check_seat_routing(_disp(model="opus", prompt="[seat:persona] x"))
    assert r.allow is False and "31-debate-tools" in r.block_message


def test_over_modeled_blocks(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="sonnet", prompt="[seat:retrieval] x")
    )
    assert r.allow is False and "retrieval" in r.block_message


def test_under_modeled_blocks(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:audit_reviewer] x")
    )
    assert r.allow is False


def test_workers_opus_over_modeled(seat_table):
    r = seat_checks.check_seat_routing(_disp(model="opus", prompt="[seat:workers] x"))
    assert r.allow is False  # workers is sonnet-only on MAX5


def test_valid_pass_zero_output(seat_table, capsys):
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] x")
    )
    assert r.allow is True and r.block_message is None
    assert capsys.readouterr().err == ""


def test_full_model_id_resolves(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="claude-opus-4-8", prompt="[seat:audit_reviewer] x")
    )
    assert r.allow is True


def test_scaled_reviewer_accepts_both(seat_table):
    assert seat_checks.check_seat_routing(
        _disp(model="sonnet", prompt="[seat:scaled_reviewer] x")
    ).allow
    assert seat_checks.check_seat_routing(
        _disp(model="opus", prompt="[seat:scaled_reviewer] x")
    ).allow


def test_whitespace_and_case_tolerant_tag(seat_table):
    assert seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat: retrieval ] x")
    ).allow
    assert seat_checks.check_seat_routing(
        _disp(model="opus", prompt="[Seat:AUDIT-REVIEWER] x")
    ).allow


def test_two_distinct_alias_tokens_unknown(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="opus-sonnet-blend", prompt="[seat:audit_reviewer] x")
    )
    assert r.allow is False and "resolve" in r.block_message.lower()


def test_repeated_identical_tags_pass(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] then [seat:retrieval]")
    )
    assert r.allow is True


def test_distinct_tags_in_window_ambiguity(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] [seat:workers] x")
    )
    assert r.allow is False and "multiple" in r.block_message.lower()


def test_nested_foreign_tag_deep_ok(seat_table):
    prompt = "[seat:audit_reviewer] REFUTE " + ("x" * 600) + " [seat:retrieval] side"
    r = seat_checks.check_seat_routing(_disp(model="opus", prompt=prompt))
    assert r.allow is True  # leading tag wins; foreign tag is beyond the window


def test_late_only_tag_distinct_message(seat_table):
    prompt = ("x" * 600) + " [seat:retrieval] late"
    r = seat_checks.check_seat_routing(_disp(model="haiku", prompt=prompt))
    assert r.allow is False and "beyond the first 500" in r.block_message


def test_tag_straddling_boundary_counts_in_window(seat_table):
    prompt = ("x" * 495) + "[seat:retrieval] straddle"
    r = seat_checks.check_seat_routing(_disp(model="haiku", prompt=prompt))
    assert r.allow is True  # match STARTS at 495 (<500) -> in window


def test_description_tag_only(seat_table):
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", description="[seat:retrieval]", prompt="body")
    )
    assert r.allow is True


def test_warn_mode_allows_with_stderr(seat_table, monkeypatch, capsys):
    monkeypatch.setenv("SEAT_ROUTING_MODE", "warn")
    r = seat_checks.check_seat_routing(_disp(prompt="[seat:retrieval] no model"))
    assert r.allow is True
    assert "SEAT ROUTING (warn)" in capsys.readouterr().err


def test_missing_table_warn_once(tmp_path, monkeypatch, capsys):
    state = tmp_path / ".claude" / "state"
    state.mkdir(parents=True)
    monkeypatch.setattr(seat_checks, "_SEAT_TABLE_PATH", state / "seat-table.json")
    monkeypatch.setattr(seat_checks, "_WARN_MARKER", state / ".seat-table-warn-emitted")
    r1 = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] x")
    )
    assert r1.allow is True and "seat-table.json" in capsys.readouterr().err
    r2 = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] x")
    )
    assert r2.allow is True and capsys.readouterr().err == ""  # warn-once


def test_corrupt_table_warn_allow(seat_table):
    (seat_table / "seat-table.json").write_text("{not json", encoding="utf-8")
    r = seat_checks.check_seat_routing(
        _disp(model="haiku", prompt="[seat:retrieval] x")
    )
    assert r.allow is True


def test_dispatcher_registers_and_routes_seat_check(seat_table):
    # Integration: the seat check is registered in the PreToolUse dispatcher's
    # _CHECKS registry and reachable on the Task/Agent branch.
    disp_path = (
        KIT_ROOT
        / "modules"
        / "10-hooks-base"
        / "files"
        / "dot-claude"
        / "hooks"
        / "pretooluse_dispatcher.py"
    )
    spec = importlib.util.spec_from_file_location("pretooluse_dispatcher", disp_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "check_seat_routing" in mod._CHECKS  # registered

    # Hook 8 (require_standing_brief) blocks a bare Agent dispatch in the
    # source-tree env (its brief path never exists), so drive the seat check
    # through its registry entry directly — the brief-sanctioned fallback. The
    # fixture-patched _SEAT_TABLE_PATH resolves because the dispatcher imports
    # the SAME cached lib.seat_checks module the fixture monkeypatched.
    blocked = mod._CHECKS["check_seat_routing"](
        _disp(model="sonnet", prompt="[seat:retrieval] x")
    )
    assert blocked.allow is False  # over-modeled -> block
    ok = mod._CHECKS["check_seat_routing"](
        _disp(model="haiku", prompt="[seat:retrieval] x")
    )
    assert ok.allow is True  # allowed model -> allow


def test_dispatch_hook8_block_short_circuits_before_seat_check(seat_table, monkeypatch):
    # Regression guard for the Task-5 branch restructure at dispatch()-level
    # (NOT the registry entry called by hand). Invariant: on the Task/Agent
    # branch a Hook-8 (require_standing_brief) BLOCK short-circuits and the seat
    # check is NEVER reached.
    #
    # Hermetic: Hook 8's real block is git-branch-dependent (it shells out to
    # `git branch --show-current` and resolves a brief path under the module
    # files/ dir — see reviewer Minor), so we monkeypatch its registry entry to
    # a deterministic block instead of leaning on repo state.
    mod = _load_dispatcher()

    _H8 = "standing-brief rule violation: STUB-BLOCK"
    monkeypatch.setitem(
        mod._CHECKS,
        "require_standing_brief",
        lambda sd: HookResult(allow=False, block_message=_H8),
    )

    # Spy on the seat check so we can prove it is NOT invoked on a block path.
    seat_calls = {"n": 0}
    _orig_seat = mod._CHECKS["check_seat_routing"]

    def _seat_spy(sd):
        seat_calls["n"] += 1
        return _orig_seat(sd)

    monkeypatch.setitem(mod._CHECKS, "check_seat_routing", _seat_spy)

    # Payload is seat-LEGAL (haiku ∈ retrieval): any block can ONLY be Hook 8's.
    r = mod.dispatch(_disp(model="haiku", prompt="[seat:retrieval] go"))

    assert r["decision"] == "block"
    assert r["message"] == _H8  # block came from Hook 8
    assert "retrieval" not in r["message"]  # NOT the seat check's reason
    assert seat_calls["n"] == 0  # seat check never reached
    # RED if someone moves the seat check ahead of Hook 8: the seat-legal
    # payload would allow at the seat check, the spy count would be 1, and the
    # short-circuit invariant would break.


def test_dispatch_hook8_allow_falls_through_to_seat_check(seat_table, monkeypatch):
    # Companion invariant: when Hook 8 ALLOWS, dispatch() falls THROUGH to the
    # seat check (the restructure changed Hook 8 from an unconditional-return to
    # capture-and-continue). A seat-ILLEGAL payload must therefore reach and be
    # blocked BY the seat check.
    mod = _load_dispatcher()

    monkeypatch.setitem(
        mod._CHECKS,
        "require_standing_brief",
        lambda sd: HookResult(allow=True, block_message=""),
    )

    # sonnet ∉ retrieval (=[haiku]) -> over-modeled -> seat check blocks.
    r = mod.dispatch(_disp(model="sonnet", prompt="[seat:retrieval] x"))

    assert r["decision"] == "block"
    assert "retrieval" in r["message"]  # the SEAT check's reason
    assert "standing-brief" not in r["message"]  # not Hook 8's
    # RED if Hook 8 reverts to an unconditional-return: an allow would return
    # {"decision": "allow"} without ever reaching the seat check, so this
    # over-modeled payload would wrongly pass.


def test_gate_evidence_has_exactly_one_seat_tag():
    # RED until Task 8 — asserts check_gate_evidence.py carries the
    # [seat:second_opinion] tag site. Task 8 adds that tag; until then this
    # finds zero tags and fails. Not a Task-4 defect. Do NOT register/patch
    # here (that is Task 8's scope).
    import re

    src = (
        KIT_ROOT
        / "modules"
        / "22-second-opinion-seat"
        / "files"
        / "dot-claude"
        / "hooks"
        / "check_gate_evidence.py"
    ).read_text(encoding="utf-8")
    occ = re.findall(r"\[seat:[^\]]*\]", src)
    assert len(occ) == 1, f"expected exactly one seat tag, found {occ}"
    m = re.fullmatch(r"\[seat:\s*([a-z_ -]+?)\s*\]", occ[0], re.IGNORECASE)
    assert (
        m
        and m.group(1).strip().lower().replace("-", "_").replace(" ", "_")
        == "second_opinion"
    )
