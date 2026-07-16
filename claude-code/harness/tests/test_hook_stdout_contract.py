"""test_hook_stdout_contract.py — allow-path stdout silence + block-path emission.

FIX-KIT-PAYLOAD-TOUCHUPS-01: both standalone PreToolUse entry points
(pretooluse_dispatcher.py, lib/pii_pattern_guard.py) must emit NOTHING on stdout
when allowing (current Claude Code schema-rejects `{"decision": "allow"}` with
"Hook JSON output validation failed") and must still emit block JSON when blocking.

Subprocess tests stage a minimal installed-shape `.claude/hooks/` tree because the
kit source spreads hook files across modules (module 27's pii guard imports module
10's `lib/__init__.py`) — they are only co-resident post-install.

Block-path negative controls run IN-PROCESS with the decision injected
(monkeypatched `dispatch` / `check_pii_patterns`), so the block cause is
deterministic — a subprocess block would depend on cwd hook state (standing brief,
seat table) and the asserted cause could silently change (advisor point D).

NOTE (MAP R1 hygiene): each staged-tree load inserts its tmp hooks dir onto the
REAL sys.path and the first in-process load caches sys.modules["lib"] across
tests — benign while every staged lib/__init__.py is byte-identical; revisit if
a test ever stages a MODIFIED lib.
"""

import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
M10_HOOKS = KIT / "modules" / "10-hooks-base" / "files" / "dot-claude" / "hooks"
M27_PII = (
    KIT
    / "modules"
    / "27-data-handling"
    / "files"
    / "dot-claude"
    / "hooks"
    / "lib"
    / "pii_pattern_guard.py"
)


def _stage_hooks(tmp_path: Path) -> Path:
    """Copy module 10's hooks tree + module 27's pii guard into an
    installed-shape `<tmp>/.claude/hooks/` and return that hooks dir."""
    hooks = tmp_path / ".claude" / "hooks"
    shutil.copytree(
        M10_HOOKS,
        hooks,
        ignore=shutil.ignore_patterns("__pycache__", ".*_cache"),
    )
    shutil.copy2(M27_PII, hooks / "lib" / "pii_pattern_guard.py")
    return hooks


def _run(script: Path, stdin_obj: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(stdin_obj),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_dispatcher_allow_emits_nothing(tmp_path):
    """Allow path → empty stdout + exit 0 (unknown tool routes to allow)."""
    hooks = _stage_hooks(tmp_path)
    p = _run(
        hooks / "pretooluse_dispatcher.py",
        {"tool_name": "NopTool", "tool_input": {}},
        tmp_path,
    )
    assert p.returncode == 0
    assert p.stdout == ""


def test_dispatcher_block_still_emits(tmp_path, monkeypatch, capsys):
    """Negative control: a block decision still reaches stdout (injected cause)."""
    hooks = _stage_hooks(tmp_path)
    mod = _load(hooks / "pretooluse_dispatcher.py", "ptd_under_test")
    monkeypatch.setattr(
        mod, "dispatch", lambda d: {"decision": "block", "message": "injected"}
    )
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO("{}"))
    with pytest.raises(SystemExit) as e:
        mod.main()
    assert e.value.code == 0
    assert json.loads(capsys.readouterr().out) == {
        "decision": "block",
        "message": "injected",
    }


def test_pii_guard_allow_emits_nothing(tmp_path):
    """Allow path → empty stdout + exit 0 (clean Write allows; check is WARN-only)."""
    hooks = _stage_hooks(tmp_path)
    p = _run(
        hooks / "lib" / "pii_pattern_guard.py",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "notes.md", "content": "hello"},
        },
        tmp_path,
    )
    assert p.returncode == 0
    assert p.stdout == ""


def test_pii_guard_block_still_emits(tmp_path, monkeypatch, capsys):
    """Negative control: the symmetric block branch still emits (injected —
    check_pii_patterns cannot block today, pii_pattern_guard.py:129-151)."""
    hooks = _stage_hooks(tmp_path)
    mod = _load(hooks / "lib" / "pii_pattern_guard.py", "pii_under_test")
    monkeypatch.setattr(
        mod,
        "check_pii_patterns",
        lambda d: mod.HookResult(allow=False, block_message="injected"),
    )
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO("{}"))
    with pytest.raises(SystemExit) as e:
        mod.main()
    assert e.value.code == 0
    assert json.loads(capsys.readouterr().out) == {
        "decision": "block",
        "message": "injected",
    }
