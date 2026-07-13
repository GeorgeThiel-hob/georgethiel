"""post_edit.py — kit-authored extraction of a single generic helper.

Extracted verbatim from a pattern-source PM-report linter module (excluded
from this kit — its other logic is a project-specific numeric-denominator
gate, out of scope here). `_post_edit_content` itself is fully generic: it
simulates a Write/Edit/MultiEdit tool call against on-disk content so a
PreToolUse guard can inspect the FULL post-edit file, not just the diff slice
the tool call carries. Every guard in this kit's `23-guards` module
(`claim_binding_guard.py`, `circularity_guard.py`, `reexec_guard.py`) imports
this function so their content-inspection logic runs against the same
simulated post-edit view.

stdlib-only — no dependency on any other kit module.
"""

from __future__ import annotations

from pathlib import Path


def _post_edit_content(file_path: Path, tool_name: str, tool_input: dict) -> str:
    """Return the file's content AFTER the edit is applied.

    For Edit and MultiEdit, simulates the replacement against the current
    on-disk content so the check operates on the full post-edit file rather
    than only the diff slice. This closes the bypass where an Edit with
    new_string="" removes a required keyword without the hook noticing.

    When the file does not yet exist on disk (new file creation via Edit
    or MultiEdit), falls back to the diff-slice (new_string / edits[*].new_string)
    — there is no existing content to simulate against.

    For Write, the supplied content replaces the file entirely — no simulation
    needed.

    Returns an empty string on any read error (fail open → allow).
    """
    if tool_name == "Write":
        return tool_input.get("content", "")

    # For Edit and MultiEdit: try to read the existing file.
    # If it doesn't exist, fall back to diff-slice checking (new_string values).
    file_exists = False
    existing = ""
    if file_path.exists():
        try:
            existing = file_path.read_text(encoding="utf-8")
            file_exists = True
        except OSError:
            return ""  # fail open on read error

    if tool_name == "Edit":
        if not file_exists:
            # New file — only diff slice available.
            return tool_input.get("new_string", "")
        old_s = tool_input.get("old_string", "")
        new_s = tool_input.get("new_string", "")
        if old_s:
            return existing.replace(old_s, new_s, 1)
        # old_string absent — treat new_string as an append (matches Claude Code
        # behaviour for unconditional inserts).
        return existing + new_s

    if tool_name == "MultiEdit":
        if not file_exists:
            # New file — only diff slices available.
            return "\n".join(
                e.get("new_string", "") for e in tool_input.get("edits", [])
            )
        result = existing
        for e in tool_input.get("edits", []):
            old_s = e.get("old_string", "")
            new_s = e.get("new_string", "")
            if old_s:
                result = result.replace(old_s, new_s, 1)
            else:
                result = result + new_s
        return result

    # Unknown tool — fall back to joining new_string fields (legacy behaviour).
    edits = tool_input.get("edits", [])
    if edits:
        return "\n".join(e.get("new_string", "") for e in edits)
    return tool_input.get("new_string", tool_input.get("content", ""))
