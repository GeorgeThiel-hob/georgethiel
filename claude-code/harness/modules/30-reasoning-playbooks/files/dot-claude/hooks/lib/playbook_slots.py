"""playbook_slots.py — kit playbook-slot presence check (module 30-reasoning-playbooks).

WARN-first, fail-open presence check (never grades slot CONTENT) for the reasoning
playbooks shipped in docs/orchestrator-playbooks/. Detects which playbook shape(s) a
branch matches, confirms each matched shape's '## Playbook slots (<shape>)' section is
present in the standing brief and/or its brief-free fallback stub, and — within each
present section — confirms every SLOT: block's fill line(s) are non-empty or explicitly
SLOT-WAIVED.

Pure core (zero I/O) + one side-effecting logger: check_playbook_slots takes plain
strings/lists and returns a PlaybookSlotsResult; the caller — this kit's
`21-pipeline-skills` module's GIT skill `--check` gate step, which the orchestrator runs
and which supplies branch/added_files/changed_paths/brief text — does all file/git I/O.

stdlib-only (no third-party imports; runs under a bare system python3).

ADAPT: this module's shape-detection keys hard-code three path conventions — the ticket
directory (_TICKETS_DIR), the analysis directory (_ANALYSES_DIR), and the MAP/verification
dossier basename (_MAP_DOSSIER_NAME) — as named module-level constants immediately below, so
an adopter using different directory names retargets them in ONE place instead of hunting
through function bodies. This is a light refactor-FOR-adaptability over the version this
module was adapted from, not a functional change.

Only two shape-detection key TYPES ship here (new-artifact-path detection and
branch-name-token detection). A third key type present in the pattern-source project this
module was adapted from — a hardcoded list of "high-stakes code path" prefixes routing to a fourth
playbook shape — is deliberately NOT ported: see this module's README ("strategy-audit.md
NOT ported"). A project that wants that fourth shape back writes its own prefix list and
shape constant here, following the same pattern as the two keys below.
"""

from __future__ import annotations

import json
import re
from collections import namedtuple
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SlotBlock = namedtuple("SlotBlock", ["name", "fill_contents", "waived"])
PlaybookSlotsResult = namedtuple(
    "PlaybookSlotsResult",
    ["warn_lines", "filled", "waived", "empty", "matched_shapes"],
)

# Shape name constants — must match the '(<shape>)' token in each playbook's own
# '## Playbook slots (<shape>)' header (docs/orchestrator-playbooks/*.md) exactly.
TICKET_SCOPING = "ticket-scoping"
DATA_ANALYSIS = "data-analysis"
BUG_INVESTIGATION = "bug-investigation"

# --- ADAPT: retarget these three constants in ONE place if your project uses different
# directory/file conventions. -----------------------------------------------------------
_TICKETS_DIR = "docs/tickets/"
_ANALYSES_DIR = "docs/analyses/"
# The MAP/verification-dossier basename every T2/T3-equivalent branch adds under
# _ANALYSES_DIR — excluded from data-analysis detection so a pure-code ticket that merely
# carries its mandatory verification dossier is never misclassified as a data-analysis
# session. A genuine data-analysis ticket is still detected via its pre-registration.md (or
# other non-dossier) artifact in the same directory.
_MAP_DOSSIER_NAME = "map-dossier.md"
_DOSSIER_BASENAMES = frozenset({_MAP_DOSSIER_NAME})
# -----------------------------------------------------------------------------------------

# Key (ii): case-insensitive substring tokens on the branch slug.
_BUG_TOKENS = ("fix", "invest", "contamination", "diag")


def _detect_shapes(
    branch_slug: str,
    added_files: list[str],
    changed_paths: list[str],  # unread by the two shipped keys below; threaded through so a
    # future third key (the documented "strategy-audit" re-add path — see README) can read it
) -> frozenset[str]:
    """Detect which playbook shape(s) this branch matches — 2 KEY TYPES, UNIONED (never
    precedence; a branch can match more than one shape):

    (i) NEW-artifact keys, checked against `added_files` (the Added-only diff, `git diff
        --diff-filter=A --name-only main...HEAD` — deliberately narrower than
        `changed_paths`, so a bare edit to an EXISTING file under _TICKETS_DIR or
        _ANALYSES_DIR never fires):
        - any path matching _TICKETS_DIR + "*.md" -> ticket-scoping
        - any path under _ANALYSES_DIR whose basename is NOT in the dossier basename
          exclusion set {_MAP_DOSSIER_NAME} -> data-analysis. The exclusion is
          load-bearing: this kit's tier system makes every T2/T3-equivalent ticket add
          _ANALYSES_DIR + "<slug>/" + _MAP_DOSSIER_NAME (the mandatory verification
          dossier), which is present on EVERY such branch including pure-code ones.
          Without the exclusion this key would classify every T2/T3-equivalent branch as
          data-analysis — a systematic false positive over the whole ticket population. A
          genuine data-analysis ticket is still detected via its pre-registration.md (or
          other non-dossier) artifact in the same directory.

    (ii) branch-name key, checked against `branch_slug`: case-insensitive substring match
         for tokens "fix", "invest", "contamination", "diag" -> bug-investigation -- UNLESS
         the slug starts with "docs-" or "chore-" (the slugified form of the docs/ / chore/
         prefixes), in which case key (ii) contributes nothing. Accepted precision loss: a
         "hotfix-" branch also matches on "fix" (acceptable — hotfixes are bug-shaped).

    Returns the UNION (frozenset) of every shape matched by any key.

    Accepted recall gaps (documented, not fixed here): (a) a bug investigation on an
    untokenized branch before any fix-shaped ticket exists is invisible to key (ii); (b) a
    data-analysis session that never opens a new analysis dir — or opens one whose only
    added file is the dossier (which the key-(i) exclusion skips) — is invisible to key (i).
    Coverage for both rides the once-per-shape playbook read, not this backstop.

    A third key type existed in the project this module was adapted from: a hardcoded list
    of code-path prefixes (execution/strategy/calibration-shaped paths) routing to a fourth
    "strategy-audit" shape. That key and its playbook are deliberately NOT ported (see
    README.md) — a project with an equivalent high-stakes-code-path concept should add its
    own prefix list and shape here, following this same pattern.
    """
    shapes: set[str] = set()

    for p in added_files:
        if p.startswith(_TICKETS_DIR) and p.endswith(".md"):
            shapes.add(TICKET_SCOPING)
        if p.startswith(_ANALYSES_DIR):
            basename = p.rsplit("/", 1)[-1]
            if basename not in _DOSSIER_BASENAMES:
                shapes.add(DATA_ANALYSIS)

    slug_lower = branch_slug.lower()
    if not (slug_lower.startswith("docs-") or slug_lower.startswith("chore-")):
        if any(tok in slug_lower for tok in _BUG_TOKENS):
            shapes.add(BUG_INVESTIGATION)

    return frozenset(shapes)


_SECTION_TERMINATOR_RE = re.compile(r"^## Playbook slots \(", re.MULTILINE)


def _find_section(text: str, shape: str) -> Optional[str]:
    """Locate '## Playbook slots (<shape>)' (anchored, MULTILINE) in `text`; return the
    body from just after that header to the next '## Playbook slots (' header (any shape)
    or end-of-text — deliberately NOT the next arbitrary '## ' header, since the playbooks
    themselves use interior level-2 headers (e.g. bug-investigation.md's '## Phase A'/
    '## Phase B'/...), so terminating at any '## ' would truncate the section at the first
    interior sub-header and silently drop every slot after it. None if the header is
    absent.

    The terminator search runs over the POST-HEADER SLICE (text[header_match.end():]),
    never over the whole text, so the section's own header can never match as its own
    terminator. The START anchor is built with re.escape(shape), defensive against a future
    shape name containing a regex metacharacter.
    """
    start_re = re.compile(
        r"^## Playbook slots \(" + re.escape(shape) + r"\)\s*$", re.MULTILINE
    )
    m = start_re.search(text)
    if m is None:
        return None
    tail = text[m.end() :]
    term_m = _SECTION_TERMINATOR_RE.search(tail)
    if term_m is None:
        return tail
    return tail[: term_m.start()]


_SLOT_START_RE = re.compile(r"^SLOT:([\w-]+)")
_SLOT_WAIVED_RE = re.compile(r"^SLOT-WAIVED:\s*")
_FILL_RE = re.compile(r"^>\s*fill\s*(?:\((\d+(?:\.\.\d+)?)\))?:\s*(.*)$")


def _parse_slots(section_text: str) -> list[SlotBlock]:
    """Walk `section_text` line by line, starting a new SlotBlock at each
    '^SLOT:([\\w-]+)' line (bounded to this section only — callers pass a body already
    isolated by _find_section) and closing it at the next SLOT: line or end-of-section.
    Within a block: every '> fill' line matches ONE combined regex covering all three
    notations ('> fill:', '> fill (2):', '> fill (1..6):' — the numbered group is optional,
    accepts a bare integer or an N..M range); its trailing content is appended to
    fill_contents. A '^SLOT-WAIVED:\\s*' line anywhere in the block sets waived=True.
    """
    blocks: list[SlotBlock] = []
    current_name: Optional[str] = None
    current_fills: list[str] = []
    current_waived = False

    def _flush() -> None:
        if current_name is not None:
            blocks.append(
                SlotBlock(
                    name=current_name,
                    fill_contents=list(current_fills),
                    waived=current_waived,
                )
            )

    for line in section_text.splitlines():
        start_m = _SLOT_START_RE.match(line)
        if start_m:
            _flush()
            current_name = start_m.group(1)
            current_fills = []
            current_waived = False
            continue
        if current_name is None:
            continue
        if _SLOT_WAIVED_RE.match(line):
            current_waived = True
            continue
        fill_m = _FILL_RE.match(line)
        if fill_m:
            current_fills.append(fill_m.group(2))

    _flush()
    return blocks


def _slot_status(slot: SlotBlock) -> str:
    """Classify a SlotBlock as 'waived' / 'empty' / 'filled'. Waived (whole slot
    suppressed, regardless of fill_contents) takes precedence; else empty if there is no
    fill line at all or any collected fill content is blank after .strip(); else filled
    (every fill line has non-blank content)."""
    if slot.waived:
        return "waived"
    if not slot.fill_contents or any(not c.strip() for c in slot.fill_contents):
        return "empty"
    return "filled"


def check_playbook_slots(
    *,
    branch: str,
    added_files: list[str],
    changed_paths: list[str],
    brief_text: Optional[str],
    brief_path: str,
    stub_text: Optional[str],
    stub_path: str,
) -> PlaybookSlotsResult:
    """Zero I/O. Detect matched shapes, then for each: require its OWN '## Playbook slots
    (<shape>)' section present in brief_text and/or stub_text (both scanned when both are
    non-None — both locations are checked when both exist); a shape whose section is absent
    from BOTH produces exactly ONE warn naming the section and the playbook file to read.
    Otherwise, every SlotBlock found in either location is classified: waived -> no warn;
    empty -> ONE warn naming SLOT:<name>, the shape section (disambiguates recurring slot
    names like 'framings'/'blast-radius' across shapes), and which file it was found in;
    filled -> no warn (one warn per SLOT, never per physical fill-line).
    """
    shapes = _detect_shapes(branch, added_files, changed_paths)
    warns: list[str] = []
    filled = waived = empty = 0

    for shape in sorted(shapes):
        locations: list[tuple[str, str]] = []
        for path, text in ((brief_path, brief_text), (stub_path, stub_text)):
            if text is None:
                continue
            body = _find_section(text, shape)
            if body is not None:
                locations.append((path, body))

        if not locations:
            playbook_file = f"docs/orchestrator-playbooks/{shape}.md"
            warns.append(
                f"missing '## Playbook slots ({shape})' section — read "
                f"{playbook_file} and add the section to the standing brief "
                f"(or the brief-free fallback stub)"
            )
            continue

        for path, body in locations:
            for slot in _parse_slots(body):
                status = _slot_status(slot)
                if status == "waived":
                    waived += 1
                elif status == "empty":
                    empty += 1
                    warns.append(
                        f"SLOT:{slot.name} is empty in "
                        f"'## Playbook slots ({shape})' ({path})"
                    )
                else:
                    filled += 1

    return PlaybookSlotsResult(
        warn_lines=warns,
        filled=filled,
        waived=waived,
        empty=empty,
        matched_shapes=tuple(sorted(shapes)),
    )


# Module-level log path — dereferenced at CALL time inside log_playbook_slots, never
# import-bound, so a test monkeypatch of _LOG_PATH redirects it (else a no-write assertion
# during a test would be vacuous).
_LOG_PATH: Path = Path.home() / ".claude" / "logs" / "playbook-slots.log"


def log_playbook_slots(
    result: PlaybookSlotsResult, branch: str, log_path: Optional[Path] = None
) -> None:
    """Append one JSON line to log_path (defaulting to the module-level _LOG_PATH,
    dereferenced at CALL time so a test monkeypatch of _LOG_PATH redirects it). Wrapped in
    its own try/except Exception: pass — never raises (best-effort)."""
    target = log_path if log_path is not None else _LOG_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "branch": branch,
                        "matched_shapes": list(result.matched_shapes),
                        "filled": result.filled,
                        "waived": result.waived,
                        "empty": result.empty,
                    }
                )
                + "\n"
            )
    except Exception:  # noqa: BLE001
        pass
