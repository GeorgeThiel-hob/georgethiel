"""tier_detection.py — mechanical T2-RISK / T3-RISK promotion from changed paths.

Used as a divergence detector at execute-phase task_checks gates. Author declares
tier in standing brief at session start; this module checks whether the actual
diff agrees with the declared tier, blocks if not.
"""

from typing import Optional

RISK_PREFIXES: tuple[str, ...] = ()


def detect_tier_promotion(diff_paths: list[str], declared_tier: str) -> Optional[str]:
    """Return promoted tier (e.g. "T2-RISK") if any diff path matches RISK_PREFIXES,
    else None. Idempotent: passing an already-RISK declared tier returns it unchanged
    when a LIVE path matches.
    """
    if not any_risk_path(diff_paths):
        return None
    base = declared_tier.replace("-RISK", "")
    return f"{base}-RISK"


def any_risk_path(paths: list[str]) -> bool:
    for p in paths:
        for prefix in RISK_PREFIXES:
            if p == prefix or p.startswith(prefix):
                return True
    return False


def effective_tier(diff_paths: list[str], declared_tier: str) -> str:
    """Re-derive the tier that should gate a /GIT ship, from the REAL diff.

    Key-guaranteed by construction: the return is ALWAYS a valid tier key
    ({T1, T2, T3, T2-RISK, T3-RISK}) for every input. A LIVE diff — or a brief
    that itself declares a -RISK tier — floors the level to >=T2 and marks it
    -RISK, so no LIVE-implicated ship can resolve to threshold 0. A non-RISK
    declared tier is returned unchanged; an unknown/typo'd tier fails SAFE to T2.

    Do NOT unify with detect_tier_promotion: that function deliberately returns
    "T1-RISK" (no level-floor) for a T1 base, and task_checks._check_tier_divergence
    depends on that no-floor behavior. The T1->T2 floor here is /GIT-only.
    """
    base = declared_tier.replace("-RISK", "")
    is_live = any_risk_path(diff_paths) or declared_tier.endswith("-RISK")
    if base not in ("T1", "T2", "T3"):
        base = "T2"  # unknown level fails safe, never 0
    if is_live:
        if base == "T1":
            base = "T2"  # no such thing as T1-RISK; LIVE floors the level to >=T2
        return f"{base}-RISK"
    return base
