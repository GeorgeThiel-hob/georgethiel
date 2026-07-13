#!/usr/bin/env bash
# Cross-platform Python 3 launcher for Claude Code hooks.
#
# Problem: Windows App Execution Aliases (AppData/.../WindowsApps/python3) are
# GUI-session stubs that resolve via `which` but fail to execute in non-interactive
# subprocesses (exit 127 "command not found"). Claude Code hooks run as non-interactive
# subprocesses, so the alias never fires.
#
# Solution: Try each candidate; the first one that actually runs Python 3 wins.
# Mac:     python3 is a real binary — passes on first try.
# Windows: python3 stub fails silently → falls through to the next candidate.
for py in python3 python /usr/local/bin/python3; do
    if "$py" -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" 2>/dev/null; then
        exec "$py" "$@"
    fi
done
echo "run_python.sh: no working Python 3 found in any candidate path" >&2
exit 1
