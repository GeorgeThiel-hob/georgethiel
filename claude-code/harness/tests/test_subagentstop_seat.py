"""Tests for AC-10 — SubagentStop delivered-model seat-mismatch detection.

Divergence from the Task-6 brief (Verified via Task-1 payload captures,
docs/superpowers/briefs/KIT-SEAT-ENFORCE-01-payload-captures.md):

The brief's illustrative fixtures read ``stdin["transcript_path"]``. Task-1
proved that in THIS Claude Code version subagent assistant entries are NOT
inlined into the parent ``transcript_path`` as ``isSidechain`` rows (0 of 2568
there); the delivered model id lives ONLY in the subagent's own
``agent_transcript_path`` (``message.model`` on its assistant entries). So the
check — and therefore these tests — read ``agent_transcript_path``. A payload
that carries only ``transcript_path`` (no ``agent_transcript_path``) is a
no-op; ``test_transcript_path_only_noop`` pins that divergence.

Import note: ``seat_checks`` does ``from . import HookResult`` (defined in
module 10-hooks-base's ``lib/__init__.py``) and ``subagentstop_log`` does
``from lib.{claim_detector,seat_checks,transcript_utils} import ...``. At
install time every module's ``dot-claude`` tree merges into ONE
``.claude/hooks/lib/``; in the unmerged repo those files sit in three separate
module dirs. Python cannot union a regular package across dirs, so — exactly as
``test_seat_checks.py`` does — we reconstruct the merged ``lib`` package here,
spanning ``__path__`` over all three module lib dirs.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parents[1]
_BASE_LIB = (
    KIT_ROOT / "modules" / "10-hooks-base" / "files" / "dot-claude" / "hooks" / "lib"
)
_L20 = (
    KIT_ROOT / "modules" / "20-tier-system" / "files" / "dot-claude" / "hooks" / "lib"
)
_G23_LIB = KIT_ROOT / "modules" / "23-guards" / "files" / "dot-claude" / "hooks" / "lib"
_G23_HOOKS = KIT_ROOT / "modules" / "23-guards" / "files" / "dot-claude" / "hooks"

# Reconstruct the installed merged `lib` package (base __init__ + all lib dirs).
_spec = importlib.util.spec_from_file_location(
    "lib",
    _BASE_LIB / "__init__.py",
    submodule_search_locations=[str(_BASE_LIB), str(_L20), str(_G23_LIB)],
)
_lib = importlib.util.module_from_spec(_spec)
sys.modules["lib"] = _lib
_spec.loader.exec_module(_lib)

sys.path.insert(0, str(_G23_HOOKS))
import subagentstop_log as ss  # noqa: E402
from lib import seat_checks  # noqa: E402


def _transcript(tmp_path, entries):
    p = tmp_path / "agent-transcript.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    return str(p)


@pytest.fixture()
def seat_table(tmp_path, monkeypatch):
    state = tmp_path / ".claude" / "state"
    state.mkdir(parents=True)
    (state / "seat-table.json").write_text(
        json.dumps(
            {
                "routing_profile": "MAX5",
                "generated_by": "test",
                "seats": {"retrieval": ["haiku"], "audit_reviewer": ["opus"]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(seat_checks, "_SEAT_TABLE_PATH", state / "seat-table.json")
    return state


def _log_capture(monkeypatch, tmp_path):
    logdir = tmp_path / "logs"
    monkeypatch.setattr(ss, "_LOG_DIR", logdir, raising=False)
    monkeypatch.setattr(
        ss, "_LOG_PATH", logdir / "subagent-failures.log", raising=False
    )
    return logdir / "subagent-failures.log"


def test_mismatch_logged_never_blocks(seat_table, tmp_path, monkeypatch):
    log = _log_capture(monkeypatch, tmp_path)
    tpath = _transcript(
        tmp_path,
        [
            {
                "type": "user",
                "message": {"role": "user", "content": "[seat:retrieval] go"},
            },
            {
                "type": "assistant",
                "message": {"model": "claude-sonnet-4-5", "content": []},
            },
        ],
    )
    # NEVER blocks: returns None regardless.
    assert ss.check_delivered_model({"agent_transcript_path": tpath}) is None
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert any(
        r["event"] == "seat-mismatch" and r["delivered_alias"] == "sonnet" for r in rows
    )


def test_match_no_log(seat_table, tmp_path, monkeypatch):
    log = _log_capture(monkeypatch, tmp_path)
    tpath = _transcript(
        tmp_path,
        [
            {
                "type": "user",
                "message": {"role": "user", "content": "[seat:retrieval] go"},
            },
            {
                "type": "assistant",
                "message": {"model": "claude-haiku-4-5", "content": []},
            },
        ],
    )
    assert ss.check_delivered_model({"agent_transcript_path": tpath}) is None
    assert not log.exists() or log.read_text().strip() == ""


def test_synthetic_skipped(seat_table, tmp_path, monkeypatch):
    log = _log_capture(monkeypatch, tmp_path)
    tpath = _transcript(
        tmp_path,
        [
            {
                "type": "user",
                "message": {"role": "user", "content": "[seat:retrieval] go"},
            },
            {"type": "assistant", "message": {"model": "<synthetic>", "content": []}},
        ],
    )
    assert ss.check_delivered_model({"agent_transcript_path": tpath}) is None
    assert not log.exists() or log.read_text().strip() == ""


def test_absent_tag_skips(seat_table, tmp_path, monkeypatch):
    log = _log_capture(monkeypatch, tmp_path)
    tpath = _transcript(
        tmp_path,
        [
            {"type": "user", "message": {"role": "user", "content": "no tag"}},
            {
                "type": "assistant",
                "message": {"model": "claude-sonnet-4-5", "content": []},
            },
        ],
    )
    assert ss.check_delivered_model({"agent_transcript_path": tpath}) is None
    assert not log.exists() or log.read_text().strip() == ""


def test_absent_transcript_path_noop(seat_table):
    # No agent_transcript_path key at all -> no-op, returns None.
    assert ss.check_delivered_model({}) is None


def test_transcript_path_only_noop(seat_table, tmp_path, monkeypatch):
    # Divergence pin: a payload carrying only the PARENT transcript_path (no
    # agent_transcript_path) must be a no-op — the check never reads
    # transcript_path (Task-1: 0 subagent models live there).
    log = _log_capture(monkeypatch, tmp_path)
    tpath = _transcript(
        tmp_path,
        [
            {
                "type": "user",
                "message": {"role": "user", "content": "[seat:retrieval] go"},
            },
            {
                "type": "assistant",
                "message": {"model": "claude-sonnet-4-5", "content": []},
            },
        ],
    )
    assert ss.check_delivered_model({"transcript_path": tpath}) is None
    assert not log.exists() or log.read_text().strip() == ""
