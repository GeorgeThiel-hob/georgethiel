"""handoff-kit/uninstall.py — reverse a recorded handoff-kit install, driven
by the single crash-safe `installer-manifest.json` written by installer.py.

Manifest-driven, single-path reversal (design spec §2.3): every delete is
provably kit-owned — guarded deletion never touches `.git`, `dest` itself,
or a path not named in the manifest. See the kit's hardening design spec
(§2.2/§2.3, Task 5).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from installer import (  # same dir; run as `python3 handoff-kit/uninstall.py`
    _BEGIN_CLAUDE_MD_RE,
    _BEGIN_GITIGNORE_RE,
    END_CLAUDE_MD,
    END_GITIGNORE,
    MANIFEST_NAME,
    MANIFEST_TMP,
    _write_text,
)

_META_JSONS = (MANIFEST_NAME, "installer-result.json", "installer-verify.json")


@dataclass
class UninstallResult:
    mode: str
    message: str
    removed: list = field(default_factory=list)
    stripped: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def _strip_marker_span(text: str, begin_re, end: str) -> tuple[str, bool]:
    """Remove ALL complete BEGIN..END spans (N18) — reverse of the merged-append.
    A BEGIN with no following END is not strippable (N19): stop and return ok=False.
    rstrip-normalizes the seam so neither joiner width leaves a blank gap (N17).

    # TODO(KIT-HARDENING): gitignore seam uses \\n not \\n\\n -- this helper
    # always rejoins head/tail with "\\n\\n" (CLAUDE.md's native merged-append
    # joiner, installer.py:359-365), but .gitignore's native joiner is a
    # single "\\n" (installer.py:462). Only matters for the rare case of
    # user content appended AFTER the kit's END marker (both head and tail
    # non-empty) — accepted per the design spec's "restores at-install-time
    # content, not byte-perfect" boundary (spec section 2.3). Pass the
    # joiner width in if exact reproduction is ever required.
    """
    ok = True
    while True:
        m = begin_re.search(text)
        if not m:
            break
        end_idx = text.find(end, m.end())
        if end_idx == -1:
            ok = False  # dangling BEGIN — not strippable
            break
        after = end_idx + len(end)
        head = text[: m.start()].rstrip("\n")
        tail = text[after:].lstrip("\n")
        if head and tail:
            text = head + "\n\n" + tail
        else:
            text = (head + tail).rstrip("\n") + ("\n" if (head or tail) else "")
    return text, ok


def _prune_empty_dirs(dest: Path, deleted_rel: list, dry_run: bool) -> None:
    dirs = set()
    for rel in deleted_rel:
        for parent in (dest / rel).parents:
            if parent == dest or dest not in parent.parents:
                continue  # never dest itself or above it (NODE-T4)
            dirs.add(parent)
    for d in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        if d.name == ".git":
            continue
        if not dry_run and d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def _remove(path: Path, rel: str, res: UninstallResult, dry_run: bool) -> None:
    if path.is_file():
        res.removed.append(rel)
        if not dry_run:
            path.unlink()


def _forced_cleanup(dest: Path, res: UninstallResult, dry_run: bool) -> UninstallResult:
    """Best-effort marker+meta cleanup when there is no usable manifest (absent or
    corrupt) + --force. Never guess-deletes payload/settings."""
    _strip_assembled(
        dest, "CLAUDE.md", _BEGIN_CLAUDE_MD_RE, END_CLAUDE_MD, "merged", res, dry_run
    )
    _strip_assembled(
        dest, ".gitignore", _BEGIN_GITIGNORE_RE, END_GITIGNORE, "merged", res, dry_run
    )
    for name in _META_JSONS + (MANIFEST_TMP,):
        _remove(dest / name, name, res, dry_run)
    res.mode = "forced-cleanup"
    res.message = "best-effort cleanup (no usable manifest): markers + meta only."
    return res


def _strip_assembled(dest, name, begin_re, end, mode, res, dry_run):
    """fresh -> delete the file; merged -> strip all spans (skip+warn on dangling)."""
    path = dest / name
    if not path.is_file():
        return
    if mode == "fresh":
        _remove(path, name, res, dry_run)
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (ValueError, OSError):
        res.skipped.append(name)
        return
    new_text, ok = _strip_marker_span(text, begin_re, end)
    if not ok:
        res.skipped.append(name)
        return
    res.stripped.append(name)
    if not dry_run:
        _write_text(path, new_text)


def _strip_settings(dest, commands, preexisting, res, dry_run):
    path = dest / ".claude" / "settings.json"
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        res.skipped.append(".claude/settings.json")
        return
    cmd_set = set(commands)
    hooks = data.get("hooks", {})
    for event in list(hooks.keys()):
        kept = []
        for e in hooks[event]:
            e["hooks"] = [
                h for h in e.get("hooks", []) if h.get("command") not in cmd_set
            ]
            if e["hooks"]:
                kept.append(e)
        hooks[event] = kept
        if not hooks[event]:  # prune now-empty event array (NODE-T1)
            del hooks[event]
    # delete iff we created it AND only an empty hooks dict remains (N14/NODE-T1);
    # else keep it with kit entries removed. Report in exactly ONE list
    # (removed XOR stripped) so --dry-run/CLI output isn't double-counted (P2-1).
    if not preexisting and set(data.keys()) == {"hooks"} and not data["hooks"]:
        _remove(path, ".claude/settings.json", res, dry_run)
    else:
        res.stripped.append(".claude/settings.json")
        if not dry_run:
            _write_text(path, json.dumps(data, indent=2) + "\n")


def uninstall(
    dest: Path, *, force: bool = False, dry_run: bool = False
) -> UninstallResult:
    dest = Path(dest).resolve()
    res = UninstallResult(mode="", message="")
    manifest_path = dest / MANIFEST_NAME
    if not manifest_path.is_file():
        if force:
            return _forced_cleanup(dest, res, dry_run)
        res.mode = "no-manifest"
        res.message = "no installer-manifest.json here; nothing removed."
        return res
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = m["files"]
        cmds = m["settings_commands"]
        cmode = m["claude_md"]["mode"]
        gmode = m["gitignore"]["mode"]
        preexisting = m["settings"]["preexisting"]
    except (ValueError, KeyError, OSError):
        if force:
            return _forced_cleanup(dest, res, dry_run)
        res.mode = "refused"
        res.message = (
            "installer-manifest.json unreadable; pass --force for best-effort cleanup."
        )
        return res

    deleted = []
    for rel in files:
        p = dest / rel
        # path-containment guard (defense-in-depth against a hand-edited
        # manifest with a `..`/absolute `files` entry escaping dest)
        if dest not in p.resolve().parents:
            res.skipped.append(rel)
            continue
        if p.is_file():
            deleted.append(rel)
            _remove(p, rel, res, dry_run)
    _strip_assembled(
        dest, "CLAUDE.md", _BEGIN_CLAUDE_MD_RE, END_CLAUDE_MD, cmode, res, dry_run
    )
    _strip_assembled(
        dest, ".gitignore", _BEGIN_GITIGNORE_RE, END_GITIGNORE, gmode, res, dry_run
    )
    _strip_settings(dest, cmds, preexisting, res, dry_run)
    for name in _META_JSONS + (MANIFEST_TMP,):
        # meta files are always dest-root; parent is never a prune candidate
        _remove(dest / name, name, res, dry_run)
    _prune_empty_dirs(dest, deleted + [".claude/settings.json"], dry_run)
    res.mode = "manifest"
    prefix = "(dry-run) " if dry_run else ""
    res.message = f"{prefix}reversed install: {len(res.removed)} removed."
    return res


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove a handoff-kit install.")
    parser.add_argument("--dest", required=True, help="destination repo root")
    parser.add_argument(
        "--force",
        action="store_true",
        help="best-effort cleanup when the manifest is absent/corrupt",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print the plan; touch nothing"
    )
    args = parser.parse_args(argv)
    res = uninstall(Path(args.dest), force=args.force, dry_run=args.dry_run)
    print(
        f"uninstall.py: mode={res.mode} removed={len(res.removed)} "
        f"stripped={len(res.stripped)} skipped={len(res.skipped)}"
    )
    print(f"uninstall.py: {res.message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
