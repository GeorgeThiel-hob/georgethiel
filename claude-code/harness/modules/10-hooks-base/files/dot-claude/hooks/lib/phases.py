"""phases.py — Advisor call phase token constants.

Single source of truth. Import from here everywhere — never hardcode phase strings.
"""

BRAINSTORM = "brainstorm"
SPEC = "spec"
PLAN = "plan"
EXECUTE = "execute"
AUDIT = "audit"
AUDIT_FIX = "audit-fix"
SHIP = "ship"

ALL_PHASES = {BRAINSTORM, SPEC, PLAN, EXECUTE, AUDIT, AUDIT_FIX, SHIP}
