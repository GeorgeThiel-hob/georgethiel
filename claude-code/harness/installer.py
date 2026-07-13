"""handoff-kit/installer.py — deterministic, stdlib-only kit installer.

Executes a resolved install-spec.json against handoff-kit/'s module library:
copy payload, merge settings.json, assemble CLAUDE.md + .gitignore, apply
ADAPT substitutions, git init, write HARNESS-VERSION.md + install report,
skill-collision check, emit installer-result.json.

Authoritative transform rules: see the kit's installer design spec (§4).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Module-list order — numeric ascending. Governs settings-fragment merge
# order, HARD-RULES block concatenation order, and DETAIL-DOCS row order
# (spec §4 steps 2 and 3).
MODULE_ORDER = [
    "00-core",
    "10-hooks-base",
    "20-tier-system",
    "21-pipeline-skills",
    "22-second-opinion-seat",
    "23-guards",
    "24-skill-delivery",
    "25-ticketing",
    "26-code-discipline",
    "27-data-handling",
    "30-reasoning-playbooks",
    "31-debate-tools",
]

# The exact ADAPT token set (spec §3, §4 step 5). RISK_PREFIXES is
# deliberately excluded — it ships as a Python default, never an ADAPT token.
ADAPT_TOKENS = (
    "PROJECT_NAME",
    "PROJECT_ONE_LINER",
    "TEST_CMD",
    "LINT_CMD",
    "TYPE_CMD",
    "SHARED_CODE_HOME",
    "TICKETING_VARIANT",
)

TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")

# Matches a hook-script path embedded anywhere inside a settings.json hook
# command string (which may chain a launcher + script, e.g. "bash
# .claude/hooks/run_python.sh .claude/hooks/pretooluse_dispatcher.py" —
# both paths match). Used only by write_verify_evidence's settings_hooks
# probe (Change 1).
_HOOK_SCRIPT_RE = re.compile(r"\.claude/hooks/[^\s\"']+\.(?:py|sh)")

BEGIN_CLAUDE_MD = "<!-- BEGIN handoff-kit harness v{version} -->"
END_CLAUDE_MD = "<!-- END handoff-kit harness -->"
BEGIN_GITIGNORE = "# BEGIN handoff-kit harness"
END_GITIGNORE = "# END handoff-kit harness"

# The two top-level docs the installer GENERATES (not payload-copied). Load-bearing
# for the uninstall manifest's delete-set. N21 trap: route this through
# emit_result_json + _verify_evidence_file_set ONLY — NEVER write_harness_version's
# hashed_paths, which deliberately excludes them (adding them breaks the AC-6 baseline).
GENERATED_TOPLEVEL_DOCS = ("HARNESS-VERSION.md", "HARNESS-INSTALL-REPORT.md")

_SKILL_VARIANT_RE = re.compile(r"^SKILL-(lite|full|github|local)\.md$")


class InstallError(Exception):
    """Raised for any spec-validation refusal or unrecoverable transform
    error. installer.py's main() catches this and exits non-zero."""


def _write_text(path: Path, text: str) -> None:
    """Write text to path with explicit newline='\\n' (Global Constraint 2 /
    N32) — prevents Windows text-mode CRLF translation from breaking
    byte-identity / the sha256 baseline. Used for every installer-WRITTEN
    file; never call Path.write_text directly elsewhere in this module."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _tokens_in_file(path: Path) -> set:
    """Return the set of {{TOKEN}} names found in path's text, or an empty
    set if the file is absent or not decodable as UTF-8 (binary payload)."""
    if not path.is_file():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return set()
    return set(TOKEN_RE.findall(text))


def _discover_payload_files(modules_root: Path, module: str, spec: dict) -> list:
    """Return the source files module's files/ payload contributes, after
    resolving skill-variant and Q3-conditional exclusions (spec §4 step 1,
    F2 filesystem-driven discovery). Excludes CLAUDE-skeleton.md,
    claude-md-block.md, gitignore-block.md, settings-fragment.json —
    those are module-level assembly inputs, never under files/, so rglob
    over files/ never sees them; no separate filtering needed for them."""
    files_root = modules_root / module / "files"
    if not files_root.is_dir():
        return []

    variant_choices = set(spec.get("variants", {}).get(module, []))
    flags = spec.get("flags", {})

    result = []
    for path in sorted(files_root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name

        m = _SKILL_VARIANT_RE.match(name)
        if m:
            # variant_choices entries are relative to dot-claude/skills/
            # (e.g. "REVIEW/SKILL-full.md" — spec §4 step 1b / design-doc
            # schema), not to files_root — compare against that root.
            skills_root = files_root / "dot-claude" / "skills"
            rel_to_skills = path.relative_to(skills_root)
            if str(rel_to_skills) not in variant_choices:
                continue  # unchosen sibling — never copied (spec §4 step 1b)
            result.append(path)
            continue

        if name == "README-template-local.md":
            if flags.get("env") != "local":
                continue  # Q3 = github — no tickets/ counterpart copied
            result.append(path)
            continue

        result.append(path)

    return result


def _destage_dot_segment(segment: str) -> str:
    """Reverse the kit's dot-staging convention: a path segment staged with
    a `dot-` prefix is renamed back to a literal dot (spec §4 step 1a) —
    `dot-claude` -> `.claude`. Segments without the prefix pass through
    unchanged."""
    if segment.startswith("dot-"):
        return "." + segment[len("dot-") :]
    return segment


def _dest_relpath(rel: Path) -> Path:
    """Compute the destination-relative path for a source file's
    files/-relative path, applying the copy-time renames (spec §4 step 1):
    dot-staging on every path segment, skill-variant suffix -> `SKILL.md`,
    and the Q3-conditional ticket-template rename. `.template` files are
    left exactly as-is (rule d) — checked first so no other rename ever
    touches them."""
    parts = [_destage_dot_segment(p) for p in rel.parts]
    if parts and parts[-1].endswith(".template"):
        return Path(*parts)

    name = parts[-1]
    m = _SKILL_VARIANT_RE.match(name)
    if m:
        parts[-1] = "SKILL.md"
    elif name == "README-template-local.md":
        parts[-1] = "README-template.md"
    return Path(*parts)


def copy_payload(spec: dict, kit_root: Path, dest: Path) -> list:
    """Copy every selected module's files/ payload to dest, applying the
    copy-time renames (spec §4 step 1). Returns the sorted list of
    dest-relative POSIX-style path strings written."""
    modules_root = kit_root / "modules"
    written = []
    for module in spec.get("modules", []):
        files_root = modules_root / module / "files"
        for src in _discover_payload_files(modules_root, module, spec):
            rel = src.relative_to(files_root)
            dest_rel = _dest_relpath(rel)
            dest_path = dest / dest_rel
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_path)  # bytes as-is, no newline translation
            written.append(dest_rel.as_posix())
    return sorted(written)


def merge_settings(spec: dict, kit_root: Path, dest: Path) -> None:
    """Assemble .claude/settings.json by deep-merging every selected
    module's settings-fragment.json, in MODULE_ORDER (spec §4 step 2:
    10-hooks-base -> 23-guards -> 27-data-handling is the only order that
    exists today, but MODULE_ORDER is walked in full so a future module's
    fragment merges correctly too). Creates the file if absent; if present
    (merged case), each event-type array is appended to, never overwritten."""
    modules_root = kit_root / "modules"
    settings_path = dest / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.is_file():
        merged = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        merged = {"hooks": {}}
    merged.setdefault("hooks", {})

    selected = set(spec.get("modules", []))
    for module in MODULE_ORDER:
        if module not in selected:
            continue
        fragment_path = modules_root / module / "settings-fragment.json"
        if not fragment_path.is_file():
            continue
        fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
        for event_type, entries in fragment.get("hooks", {}).items():
            merged["hooks"].setdefault(event_type, [])
            merged["hooks"][event_type].extend(entries)

    _write_text(settings_path, json.dumps(merged, indent=2) + "\n")


def detect_claude_md_mode(dest: Path) -> str:
    """Fresh vs merged is DETECTED from dest's current state, never trusted
    as a spec input (Global Constraint 3 / Step-0 N3)."""
    return "merged" if (dest / "CLAUDE.md").is_file() else "fresh"


MANIFEST_NAME = "installer-manifest.json"
MANIFEST_TMP = "installer-manifest.json.tmp"


def detect_gitignore_mode(dest: Path) -> str:
    """Fresh vs merged for .gitignore, detected from dest state (mirror of
    detect_claude_md_mode — the assemble step re-detects the same signal)."""
    return "merged" if (dest / ".gitignore").is_file() else "fresh"


def _planned_payload_files(spec: dict, kit_root: Path) -> list:
    """The pre-copy twin of copy_payload: the sorted dest-relative POSIX paths
    the payload WILL occupy. Uses the same _discover_payload_files + _dest_relpath
    copy_payload uses, so the sets are equal by construction (MAP parity)."""
    modules_root = kit_root / "modules"
    planned = []
    for module in spec.get("modules", []):
        files_root = modules_root / module / "files"
        for src in _discover_payload_files(modules_root, module, spec):
            rel = src.relative_to(files_root)
            planned.append(_dest_relpath(rel).as_posix())
    return sorted(planned)


def _derive_settings_commands(spec: dict, kit_root: Path) -> list:
    """The exact hook command strings the selected modules' settings fragments
    install — mirrors merge_settings' selection (MODULE_ORDER n selected,
    fragment.is_file()); never hardcoded. Commands are stored verbatim (no ADAPT
    token in any fragment), so uninstall matches them by exact string (AC-3)."""
    modules_root = kit_root / "modules"
    selected = set(spec.get("modules", []))
    commands = []
    for module in MODULE_ORDER:
        if module not in selected:
            continue
        fragment_path = modules_root / module / "settings-fragment.json"
        if not fragment_path.is_file():
            continue
        fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
        for entries in fragment.get("hooks", {}).values():
            for entry in entries:
                for hook in entry.get("hooks", []):
                    cmd = hook.get("command")
                    if cmd is not None:
                        commands.append(cmd)
    return commands


def write_install_manifest(spec: dict, kit_root: Path, dest: Path) -> None:
    """Write installer-manifest.json ATOMICALLY (temp + os.replace) — the single
    crash-safe uninstall record. MUST be called AFTER the AC-4/AC-5 guards pass and
    BEFORE copy_payload (G5). Detects modes from dest's CURRENT (pre-install) state."""
    manifest = {
        "manifest_version": 1,
        "modules": list(spec.get("modules", [])),
        "files": _planned_payload_files(spec, kit_root) + list(GENERATED_TOPLEVEL_DOCS),
        "claude_md": {"path": "CLAUDE.md", "mode": detect_claude_md_mode(dest)},
        "gitignore": {"path": ".gitignore", "mode": detect_gitignore_mode(dest)},
        "settings": {
            "path": ".claude/settings.json",
            "preexisting": (dest / ".claude" / "settings.json").is_file(),
        },
        "settings_commands": _derive_settings_commands(spec, kit_root),
    }
    tmp = dest / MANIFEST_TMP
    _write_text(tmp, json.dumps(manifest, indent=2) + "\n")
    os.replace(tmp, dest / MANIFEST_NAME)


def _strip_marker_line(text: str, marker: str) -> str:
    """Remove exactly one `<!-- MARKER -->\\n` line, leaving the body that
    follows untouched. Used for PROJECT-OVERVIEW and PERMITTED, whose
    skeleton body IS the content to install (spec §4 step 3: "skeleton
    static text") — only the HTML-comment scaffolding is dropped."""
    pattern = re.compile(r"<!-- " + re.escape(marker) + r" -->\n")
    new_text, n = pattern.subn("", text, count=1)
    if n != 1:
        raise InstallError(f"CLAUDE-skeleton.md: slot marker {marker!r} not found")
    return new_text


def _replace_slot_body(text: str, marker: str, content: str) -> str:
    """Remove the `<!-- MARKER -->\\n` line AND replace the placeholder body
    up to (not including) the next `\\n---` with `content`. Used for
    HARD-RULES, WORKFLOW-TABLE, DETAIL-DOCS-POINTER-TABLE, whose skeleton
    body is a placeholder/example that must not survive assembly.

    The replacement is a function, not a string: passing `content` as a
    string replacement to `re.subn` would make `re` interpret backslash
    sequences in it (`\\1`, `\\g<..>`, `\\d`, ...) as backreferences/escapes
    — a latent crash if any block/harness-doc content ever contains a
    literal backslash. A lambda returns `content` verbatim.

    The lambda also re-appends the trailing `\\n` the lazy `(?=\\n---)`
    lookahead consumes from the skeleton's placeholder body, so the
    skeleton's blank line before the `---` divider survives: `content` +
    `\\n` (this call) + `\\n---` (the untouched remainder) == `content\\n\\n---`,
    matching the reference CLAUDE.md's slot-to-divider spacing."""
    pattern = re.compile(
        r"<!-- " + re.escape(marker) + r" -->\n.*?(?=\n---)",
        re.DOTALL,
    )
    new_text, n = pattern.subn(lambda m: content.rstrip("\n") + "\n", text, count=1)
    if n != 1:
        raise InstallError(f"CLAUDE-skeleton.md: slot marker {marker!r} not found")
    return new_text


_POINTER_ROW_RE = re.compile(
    r"^<!-- POINTER-ROW:\s*(?P<when>[^|]+?)\s*\|\s*(?P<what>[^>]+?)\s*-->\s*\n"
)


def _pointer_row_text(doc_path: Path, module: str) -> tuple:
    """Read the two prose cells for a DETAIL-DOCS row from an optional
    leading `<!-- POINTER-ROW: <when> | <what> -->` comment in the
    module's harness doc; fall back to the deterministic, domain-neutral
    default when absent (spec §4 step 3 — this ticket ships NO POINTER-ROW
    comment in any real kit doc, Global Constraint 4, so every module
    falls to this fallback in practice; the comment path is exercised only
    by a temp-dir fixture in Task 11)."""
    text = doc_path.read_text(encoding="utf-8")
    m = _POINTER_ROW_RE.match(text)
    if m:
        return m.group("when").strip(), m.group("what").strip()
    return f"per-{module} work", f"{module} reference"


def _build_detail_docs_rows(modules_root: Path, selected: list) -> str:
    """3-cell DETAIL-DOCS-POINTER-TABLE, one row per installed
    docs/harness/<module>.md, in MODULE_ORDER, skipping 00-core (already
    pre-seeded in the skeleton — spec §4 step 3) and any module that ships
    no harness doc at all (10-hooks-base, 30-reasoning-playbooks — see the
    module-list-order note at the top of this plan)."""
    header = (
        "| Doc | When to read | What's in it |\n|-----|--------------|--------------|\n"
    )
    seeded_row = (
        "| `docs/harness/00-core.md` | Before relying on any hard rule above, "
        "or on memory/DoD conventions | Full text + rationale for the hard "
        "rules, memory conventions, Definition-of-Done shape |\n"
    )
    rows = [seeded_row]
    for module in MODULE_ORDER:
        if module == "00-core" or module not in selected:
            continue
        doc_path = modules_root / module / "files" / "docs" / "harness" / f"{module}.md"
        if not doc_path.is_file():
            continue
        when, what = _pointer_row_text(doc_path, module)
        rows.append(f"| `docs/harness/{module}.md` | {when} | {what} |\n")
    return header + "".join(rows)


def _hard_rules_blocks(modules_root: Path, selected: list) -> str:
    blocks = []
    for module in MODULE_ORDER:
        if module not in selected:
            continue
        block_path = modules_root / module / "claude-md-block.md"
        if block_path.is_file():
            blocks.append(block_path.read_text(encoding="utf-8").rstrip("\n"))
    return "\n\n".join(blocks) + "\n"


def _assemble_fresh_claude_md(spec: dict, kit_root: Path) -> str:
    modules_root = kit_root / "modules"
    selected = spec.get("modules", [])
    text = (modules_root / "00-core" / "CLAUDE-skeleton.md").read_text(encoding="utf-8")

    text = _strip_marker_line(text, "PROJECT-OVERVIEW")
    text = _strip_marker_line(text, "PERMITTED")
    text = _replace_slot_body(
        text, "HARD-RULES", _hard_rules_blocks(modules_root, selected)
    )
    rigor = spec["rigor"]
    workflow_table = (
        modules_root / "00-core" / f"workflow-table-{rigor}.md"
    ).read_text(encoding="utf-8")
    text = _replace_slot_body(text, "WORKFLOW-TABLE", workflow_table)
    text = _replace_slot_body(
        text,
        "DETAIL-DOCS-POINTER-TABLE",
        _build_detail_docs_rows(modules_root, selected),
    )
    return text


def _assemble_merged_claude_md(spec: dict, kit_root: Path, existing_text: str) -> str:
    modules_root = kit_root / "modules"
    selected = spec.get("modules", [])
    hard_rules = _hard_rules_blocks(modules_root, selected).rstrip("\n")
    rigor = spec["rigor"]
    workflow_table = (
        (modules_root / "00-core" / f"workflow-table-{rigor}.md")
        .read_text(encoding="utf-8")
        .rstrip("\n")
    )
    detail_rows = _build_detail_docs_rows(modules_root, selected).rstrip("\n")
    version = spec.get("kit_version", "0.0.0")

    section = (
        f"\n\n{BEGIN_CLAUDE_MD.format(version=version)}\n\n"
        f"## Hard rules\n\n{hard_rules}\n\n"
        f"## Workflow\n\n{workflow_table}\n\n"
        f"## Detail docs\n\n{detail_rows}\n\n"
        f"{END_CLAUDE_MD}\n"
    )
    return existing_text.rstrip("\n") + section


def assemble_claude_md(spec: dict, kit_root: Path, dest: Path) -> str:
    """Assemble dest/CLAUDE.md. Detects fresh vs merged from dest's current
    state (Global Constraint 3). Returns the detected mode for the caller
    to record in HARNESS-VERSION.md. Tokens are left intact for
    apply_adapt (Task 7) to substitute afterward."""
    claude_md_path = dest / "CLAUDE.md"
    mode = detect_claude_md_mode(dest)
    if mode == "fresh":
        text = _assemble_fresh_claude_md(spec, kit_root)
    else:
        existing = claude_md_path.read_text(encoding="utf-8")
        text = _assemble_merged_claude_md(spec, kit_root, existing)
    _write_text(claude_md_path, text)
    return mode


def load_and_validate_spec(spec_path: str, kit_root: Path) -> dict:
    """Load install-spec.json and validate it against the kit at kit_root.

    Raises InstallError (never returns a partially-valid spec) when:
      - a named module does not exist under kit_root/modules/
      - a named skill/file variant does not exist on disk
      - 25-ticketing is selected but adapt['TICKETING_VARIANT'] is missing
      - any {{TOKEN}} reachable in the selected payload or the CLAUDE.md
        assembly inputs (skeleton + selected claude-md-block.md files +
        the per-rigor workflow-table snippet — Step-0 N26) has no value
        in spec['adapt']
    """
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    modules_root = kit_root / "modules"
    modules = spec.get("modules", [])

    for module in modules:
        if not (modules_root / module).is_dir():
            raise InstallError(
                f"unknown module in spec: {module!r} "
                f"(no directory at {modules_root / module})"
            )

    for module, paths in spec.get("variants", {}).items():
        for rel in paths:
            candidate = modules_root / module / "files" / "dot-claude" / "skills" / rel
            if not candidate.is_file():
                raise InstallError(
                    f"variant not found on disk: module {module!r} names "
                    f"{rel!r} (looked for {candidate})"
                )

    adapt = spec.get("adapt", {})
    if "25-ticketing" in modules and not adapt.get("TICKETING_VARIANT"):
        raise InstallError(
            "25-ticketing is selected but adapt.TICKETING_VARIANT is missing"
        )

    found_tokens = set()
    for module in modules:
        for path in _discover_payload_files(modules_root, module, spec):
            found_tokens |= _tokens_in_file(path)

    found_tokens |= _tokens_in_file(modules_root / "00-core" / "CLAUDE-skeleton.md")
    for module in modules:
        block = modules_root / module / "claude-md-block.md"
        found_tokens |= _tokens_in_file(block)

    rigor = spec.get("rigor")
    if rigor:
        found_tokens |= _tokens_in_file(
            modules_root / "00-core" / f"workflow-table-{rigor}.md"
        )

    missing = sorted(t for t in found_tokens if t not in adapt)
    if missing:
        raise InstallError(
            f"unresolved ADAPT token(s): {', '.join(missing)} — "
            f"add value(s) to spec['adapt']"
        )

    return spec


def assemble_gitignore(spec: dict, kit_root: Path, dest: Path) -> str:
    """Assemble dest/.gitignore from 00-core/gitignore-block.md. Both fresh
    and merged wrap the content in `# BEGIN/END handoff-kit harness`
    markers (spec §4 step 4). Returns the detected mode."""
    block = (
        (kit_root / "modules" / "00-core" / "gitignore-block.md")
        .read_text(encoding="utf-8")
        .rstrip("\n")
    )
    section = f"{BEGIN_GITIGNORE}\n{block}\n{END_GITIGNORE}\n"

    gitignore_path = dest / ".gitignore"
    mode = "merged" if gitignore_path.is_file() else "fresh"
    if mode == "merged":
        existing = gitignore_path.read_text(encoding="utf-8").rstrip("\n")
        text = existing + "\n" + section if existing else section
    else:
        text = section
    _write_text(gitignore_path, text)
    return mode


def apply_adapt(dest: Path, written_paths: list, adapt: dict) -> None:
    """Replace every {{TOKEN}} from adapt in the copied payload files
    (written_paths, from copy_payload) and the assembled CLAUDE.md (spec §4
    step 5). Then runs the "no {{TOKEN}} survives" guard over exactly
    these installer-WRITTEN files (Global Constraint 5) — never over
    settings.json/.gitignore (the kit never templates them) or
    HARNESS-VERSION.md/the install report (which legitimately document
    {{TOKEN}} literals in their ADAPT-values table). Raises InstallError
    if any token survives."""
    targets = [dest / rel for rel in written_paths]
    claude_md = dest / "CLAUDE.md"
    if claude_md.is_file():
        targets.append(claude_md)

    for path in targets:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary payload file — no tokens possible
        if "{{" not in text:
            continue
        new_text = text
        for token, value in adapt.items():
            new_text = new_text.replace("{{" + token + "}}", value)
        if new_text != text:
            _write_text(path, new_text)

    survivors = []
    for path in targets:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = TOKEN_RE.findall(text)
        if found:
            survivors.append((path, sorted(set(found))))

    if survivors:
        detail = "; ".join(f"{p}: {t}" for p, t in survivors)
        raise InstallError(f"ADAPT token(s) survived substitution: {detail}")


def git_init(dest: Path) -> bool:
    """git init at dest if .git is absent (spec §4 step 6 — the sole
    subprocess call, Global Constraint 1). Returns True if it ran, False
    if a repo already existed."""
    if (dest / ".git").exists():
        return False
    try:
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=str(dest),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise InstallError(f"git init failed: {exc.stderr or exc}") from exc
    return True


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _section_scoped_bytes(path: Path, begin_re, end_marker: str) -> bytes:
    """Bytes strictly between a begin-marker match and the next occurrence
    of end_marker, both markers excluded (spec §4 step 7 — section-scoped
    hash for a MERGED CLAUDE.md/.gitignore)."""
    text = path.read_text(encoding="utf-8")
    m = begin_re.search(text)
    if not m:
        raise InstallError(f"{path}: missing BEGIN marker for section-scoped hash")
    end_idx = text.index(end_marker, m.end())
    return text[m.end() : end_idx].encode("utf-8")


_BEGIN_CLAUDE_MD_RE = re.compile(r"<!-- BEGIN handoff-kit harness v[^>]*-->")
_BEGIN_GITIGNORE_RE = re.compile(re.escape(BEGIN_GITIGNORE))


def hash_installed_file(
    path: Path, dest: Path, claude_md_mode: str, gitignore_mode: str
) -> str:
    """Post-ADAPT per-file sha256 (spec §4 step 7). Section-scoped for a
    MERGED CLAUDE.md/.gitignore; whole-file for everything else, including
    a FRESH CLAUDE.md/.gitignore (spec: "whole-file for everything else")."""
    rel = path.relative_to(dest).as_posix()
    if rel == "CLAUDE.md" and claude_md_mode == "merged":
        data = _section_scoped_bytes(path, _BEGIN_CLAUDE_MD_RE, END_CLAUDE_MD)
    elif rel == ".gitignore" and gitignore_mode == "merged":
        data = _section_scoped_bytes(path, _BEGIN_GITIGNORE_RE, END_GITIGNORE)
    else:
        data = path.read_bytes()
    return sha256_of_bytes(data)


def write_harness_version(
    spec: dict,
    dest: Path,
    written_paths: list,
    claude_md_mode: str,
    gitignore_mode: str,
    now_iso: str,
) -> None:
    """Write HARNESS-VERSION.md: kit version, resolved profiles/flags,
    overrides, module list, ADAPT values, detected modes, install date, and
    the post-ADAPT per-file sha256 baseline (spec §4 step 7)."""
    hashed_paths = sorted(
        set(written_paths)
        | {
            ".claude/settings.json",
            ".gitignore",
            "CLAUDE.md",
        }
    )
    lines = ["# Harness install record", ""]
    lines.append(f"- **Kit version:** {spec.get('kit_version', '0.0.0')}")
    lines.append(f"- **Install date:** {now_iso}")
    lines.append(f"- **Resolved rigor profile:** {spec.get('rigor')}")
    lines.append(f"- **Resolved routing profile:** {spec.get('routing')}")
    lines.append(f"- **`claude_md_mode`:** {claude_md_mode}")
    lines.append(f"- **`gitignore_mode`:** {gitignore_mode}")
    lines.append("")
    lines.append("## Modules installed")
    lines.append("")
    lines.append(", ".join(f"`{m}`" for m in spec.get("modules", [])))
    lines.append("")
    lines.append("## Flags")
    lines.append("")
    for k, v in spec.get("flags", {}).items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Overrides")
    lines.append("")
    overrides = spec.get("overrides", [])
    lines.append("None." if not overrides else "\n".join(f"- {o}" for o in overrides))
    lines.append("")
    lines.append("## ADAPT values substituted")
    lines.append("")
    for token in ADAPT_TOKENS:
        if token in spec.get("adapt", {}):
            lines.append(f"| `{{{{{token}}}}}` | {spec['adapt'][token]} |")
    lines.append("")
    lines.append("## Post-ADAPT per-file hash baseline (SHA-256)")
    lines.append("")
    lines.append("```")
    for rel in hashed_paths:
        path = dest / rel
        if not path.is_file():
            continue
        digest = hash_installed_file(path, dest, claude_md_mode, gitignore_mode)
        lines.append(f"{digest}  {rel}")
    lines.append("```")
    lines.append("")
    _write_text(dest / "HARNESS-VERSION.md", "\n".join(lines) + "\n")


def write_install_report(spec: dict, dest: Path, warnings: list) -> None:
    """Write HARNESS-INSTALL-REPORT.md: modules, ADAPT edits, warnings,
    restart instruction (spec §4 step 8)."""
    lines = ["# Harness Install Report", "", "## Modules installed", ""]
    lines.append(", ".join(f"`{m}`" for m in spec.get("modules", [])))
    lines.append("")
    lines.append("## ADAPT edits")
    lines.append("")
    for token in ADAPT_TOKENS:
        if token in spec.get("adapt", {}):
            lines.append(f"- `{{{{{token}}}}}` -> {spec['adapt'][token]}")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        lines.extend(f"- WARN: {w}" for w in warnings)
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Next step")
    lines.append("")
    lines.append(
        "**Restart the Claude Code session** — a `.claude/skills/` directory "
        "created mid-session is only discovered after a restart."
    )
    lines.append("")
    _write_text(dest / "HARNESS-INSTALL-REPORT.md", "\n".join(lines) + "\n")


def skill_collision_glob(dest: Path, home: Path | None = None) -> list:
    """For each skill just installed under dest/.claude/skills/, Glob for a
    same-named GLOBAL skill at ~/.claude/skills/<name>/ and
    ~/.claude/skills/<name>.md (spec §4 step 9 — both path forms). Returns
    a list of warning strings; empty if no collisions."""
    home = home or Path.home()
    skills_dir = dest / ".claude" / "skills"
    if not skills_dir.is_dir():
        return []
    warnings = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        global_dir = home / ".claude" / "skills" / name
        global_file = home / ".claude" / "skills" / f"{name}.md"
        if global_dir.is_dir():
            warnings.append(
                f"global skill directory shadows installed skill: {global_dir}"
            )
        if global_file.is_file():
            warnings.append(f"global skill file shadows installed skill: {global_file}")
    return warnings


def emit_result_json(
    dest: Path,
    written_paths: list,
    warnings: list,
    claude_md_mode: str,
    gitignore_mode: str,
) -> None:
    """Write installer-result.json — files written, warnings, resolved
    decisions — so the VERIFY pass confirms rather than re-derives
    (spec §4 step 10)."""
    result = {
        "files_written": sorted(
            set(written_paths)
            | {".claude/settings.json", ".gitignore", "CLAUDE.md"}
            | set(GENERATED_TOPLEVEL_DOCS)
        ),
        "warnings": warnings,
        "claude_md_mode": claude_md_mode,
        "gitignore_mode": gitignore_mode,
    }
    _write_text(dest / "installer-result.json", json.dumps(result, indent=2) + "\n")


def _verify_evidence_file_set(written_paths: list) -> list:
    """The dest-relative paths installer-verify.json hashes (Change 1's
    "files" list): the same set emit_result_json records as
    files_written — payload plus every installer-generated top-level file,
    including the two docs that legitimately carry {{TOKEN}} literals in
    prose (HARNESS-VERSION.md, HARNESS-INSTALL-REPORT.md); those are hashed
    here but excluded from the token scan below."""
    return sorted(
        set(written_paths)
        | {".claude/settings.json", ".gitignore", "CLAUDE.md"}
        | set(GENERATED_TOPLEVEL_DOCS)
    )


def _token_scan_target_set(written_paths: list) -> list:
    """The dest-relative paths the {{TOKEN}} residue scan covers: exactly
    apply_adapt's own target set (written_paths + CLAUDE.md) plus the two
    files apply_adapt never templates but a residue in would be just as
    real a bug (.gitignore, .claude/settings.json). Excludes
    HARNESS-VERSION.md / HARNESS-INSTALL-REPORT.md (spec: those legitimately
    document {{TOKEN}} literals in their ADAPT-values tables)."""
    return sorted(
        set(written_paths) | {"CLAUDE.md", ".gitignore", ".claude/settings.json"}
    )


def _scan_token_residues(dest: Path, rels: list) -> tuple:
    """Actual regex scan (TOKEN_RE) over rels, mirroring apply_adapt's own
    file-handling: skip absent files, skip UnicodeDecodeError (binary)
    files. Returns (files_scanned, residues) — residues is a list of
    {"path", "line", "token"} dicts, one per surviving {{TOKEN}} match."""
    files_scanned = 0
    residues = []
    for rel in rels:
        path = dest / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files_scanned += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in TOKEN_RE.finditer(line):
                residues.append({"path": rel, "line": lineno, "token": match.group(1)})
    return files_scanned, residues


def _settings_hook_scripts(dest: Path) -> list:
    """Walk the installed .claude/settings.json's hooks structure and
    extract every hook-script path embedded in a command string (a command
    may chain a launcher + script — both are extracted). Returns a list of
    {"event", "script", "exists"} dicts; "exists" is a real filesystem
    check against dest, never inferred from written_paths."""
    settings_path = dest / ".claude" / "settings.json"
    if not settings_path.is_file():
        return []
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    result = []
    for event_type, entries in settings.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                for match in _HOOK_SCRIPT_RE.finditer(command):
                    script = match.group(0)
                    result.append(
                        {
                            "event": event_type,
                            "script": script,
                            "exists": (dest / script).is_file(),
                        }
                    )
    return result


def write_verify_evidence(
    spec: dict,
    dest: Path,
    written_paths: list,
    now_iso: str,
    skill_collisions: list | None = None,
) -> None:
    """Write installer-verify.json: post-install verification evidence so a
    VERIFY pass confirms with real filesystem probes instead of re-deriving
    them by hand (efficiency-audit rec 2; see the kit's build notes §5c). META like
    installer-result.json: never appended to written_paths/files_written,
    never hashed into HARNESS-VERSION.md's baseline, never counted in the
    install report.

    `skill_collisions`, when provided, MUST be the already-computed return
    value of this install's single `skill_collision_glob(dest)` call (main()
    reuses it rather than globbing twice); when omitted (e.g. a caller
    invoking this function directly, as the test suite's negative controls
    do) it is computed fresh here."""
    file_set = _verify_evidence_file_set(written_paths)
    files = []
    for rel in file_set:
        path = dest / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({"path": rel, "sha256": sha256_of_bytes(data), "bytes": len(data)})

    scan_targets = _token_scan_target_set(written_paths)
    files_scanned, residues = _scan_token_residues(dest, scan_targets)

    if skill_collisions is None:
        skill_collisions = skill_collision_glob(dest)

    evidence = {
        "files": files,
        "token_scan": {"files_scanned": files_scanned, "residues": residues},
        "settings_hooks": _settings_hook_scripts(dest),
        "skill_collisions": skill_collisions,
        "generated_at": now_iso,
    }
    _write_text(
        dest / "installer-verify.json",
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
    )


_PRIOR_INSTALL_HOOK_MARKER = ".claude/hooks/run_python.sh"
_PRIOR_INSTALL_MARKER = "BEGIN handoff-kit"


def _prior_install_evidence(dest: Path) -> bool:
    """True if ANY of the 6 prior-install signals is present at dest (AC-4):
    installer-manifest.json, installer-result.json, installer-verify.json,
    HARNESS-VERSION.md, a BEGIN handoff-kit marker in CLAUDE.md or
    .gitignore, or a settings.json hook command embedding run_python.sh.
    False means no evidence — a genuine fresh install. Called ONLY from
    main() (never from a unit helper), so the AC-6 / merged-unit tests —
    which invoke the unit functions directly against a fresh dest — stay
    green (design spec §3)."""
    if (dest / MANIFEST_NAME).is_file():
        return True
    if (dest / "installer-result.json").is_file():
        return True
    if (dest / "installer-verify.json").is_file():
        return True
    if (dest / "HARNESS-VERSION.md").is_file():
        return True

    for name in ("CLAUDE.md", ".gitignore"):
        path = dest / name
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if _PRIOR_INSTALL_MARKER in text:
                return True

    settings_path = dest / ".claude" / "settings.json"
    if settings_path.is_file():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            # ValueError covers json.JSONDecodeError AND UnicodeDecodeError
            # (both subclass it); OSError covers an unreadable file. An
            # unparseable settings.json contributes no signal rather than
            # crashing the guard (consistent with the marker branch above).
            settings = {}
        for entries in settings.get("hooks", {}).values():
            for entry in entries:
                for hook in entry.get("hooks", []):
                    if _PRIOR_INSTALL_HOOK_MARKER in (hook.get("command") or ""):
                        return True

    return False


def _dest_overwrite_conflicts(spec: dict, kit_root: Path, dest: Path) -> list:
    """Return the sorted dest-relative POSIX paths where a payload file this
    install would write already exists at dest with DIFFERING bytes (AC-5).
    Mirrors copy_payload's own discovery/rename walk exactly (same
    _discover_payload_files + _dest_relpath calls, same loop shape as
    _planned_payload_files) so the compared set is exactly what
    copy_payload would write — never a parallel/approximate list. A dest
    file already byte-identical to the source is NOT a conflict (re-running
    into unchanged output is not a hostile overwrite); AC-4 handles the
    "this is our own prior install" case separately, so this check only
    needs to catch a genuinely foreign file."""
    modules_root = kit_root / "modules"
    conflicts = []
    for module in spec.get("modules", []):
        files_root = modules_root / module / "files"
        for src in _discover_payload_files(modules_root, module, spec):
            rel = src.relative_to(files_root)
            dest_rel = _dest_relpath(rel)
            dest_path = dest / dest_rel
            if dest_path.is_file() and dest_path.read_bytes() != src.read_bytes():
                conflicts.append(dest_rel.as_posix())
    return sorted(conflicts)


def main(argv: list | None = None) -> int:
    """CLI entry point: orchestrate the full install pipeline against
    args.dest. Order is load-bearing (spec §2.1/§3, G5): validate -> AC-4
    prior-install guard -> AC-5 dest-overwrite guard (both skippable via
    --force) -> write_install_manifest -> copy -> merge settings ->
    assemble CLAUDE.md -> assemble .gitignore -> apply_adapt (after
    assembly, so it substitutes tokens in both the copied payload and the
    assembled CLAUDE.md) -> git_init -> write_harness_version (hashes
    POST-ADAPT bytes, so it must run after apply_adapt) ->
    skill_collision_glob -> write_install_report -> write_verify_evidence
    (reuses skill_collision_glob's result — never calls it twice) ->
    emit_result_json. The manifest is written only AFTER both guards pass
    (G5 — a refused/--force-declined install must never record the user's
    own files for uninstall.py to later delete). Returns 0 on success, 1 on
    InstallError (message printed to stderr)."""
    parser = argparse.ArgumentParser(description="Install the handoff-kit harness.")
    parser.add_argument("--spec", required=True, help="path to install-spec.json")
    parser.add_argument("--dest", required=True, help="destination repo root")
    parser.add_argument(
        "--now",
        required=False,
        default=None,
        help=(
            "ISO-8601 install timestamp (optional — when omitted, the "
            "installer self-stamps datetime.now(timezone.utc).isoformat())"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "skip the prior-install guard (AC-4) and the dest-overwrite "
            "guard (AC-5). Trades away the crash-safety guarantee that the "
            "install manifest never records a path the install did not "
            "own — a crash between the manifest write and a conflicting "
            "file's copy could leave a user's original bytes on disk yet "
            "recorded as kit-owned."
        ),
    )
    args = parser.parse_args(argv)
    now_iso = (
        args.now if args.now is not None else datetime.now(timezone.utc).isoformat()
    )

    kit_root = Path(__file__).resolve().parent
    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    try:
        spec = load_and_validate_spec(args.spec, kit_root)

        if not args.force and _prior_install_evidence(dest):
            raise InstallError(
                f"prior handoff-kit install detected at {dest} — run "
                "uninstall.py first, then re-run the installer (or pass "
                "--force to overwrite)"
            )

        if not args.force:
            conflicts = _dest_overwrite_conflicts(spec, kit_root, dest)
            if conflicts:
                raise InstallError(
                    "dest has pre-existing file(s) that differ from the kit "
                    f"payload: {', '.join(conflicts)} — move them, or pass "
                    "--force to overwrite"
                )

        write_install_manifest(spec, kit_root, dest)
        written = copy_payload(spec, kit_root, dest)
        merge_settings(spec, kit_root, dest)
        claude_md_mode = assemble_claude_md(spec, kit_root, dest)
        gitignore_mode = assemble_gitignore(spec, kit_root, dest)
        apply_adapt(dest, written, spec.get("adapt", {}))
        git_init(dest)
        write_harness_version(
            spec, dest, written, claude_md_mode, gitignore_mode, now_iso
        )
        warnings = skill_collision_glob(dest)
        write_install_report(spec, dest, warnings)
        write_verify_evidence(spec, dest, written, now_iso, skill_collisions=warnings)
        emit_result_json(dest, written, warnings, claude_md_mode, gitignore_mode)
    except InstallError as exc:
        print(f"installer.py: error: {exc}", file=sys.stderr)
        return 1

    print(f"installer.py: installed {len(written)} files to {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
