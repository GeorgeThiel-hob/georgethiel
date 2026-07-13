"""Shared claim-detection lib.

Pure, schema-free: text in -> findings out. Imported by subagentstop_log.py
(SubagentStop, log-only, back-compat) and stop_citation_guard.py (main-thread Stop).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FIVE_CLASSES = (
    "coefficient-vs-intuition",
    "staleness",
    "snapshot-vs-permanent",
    "already-implemented",
    "inferred-dependency",
)

# Code-structure triggers — VERBATIM from subagentstop_log.py:85-96 (back-compat; catch 0/7 alone).
CODE_STRUCTURE_PATTERNS = [
    re.compile(
        r"\b(does|will|always|never|currently)\b.*\b(fires?|runs?|executes?|returns?|matches?|fails?|skips?)\b",
        re.I,
    ),
    re.compile(
        r"\b(the|this) (function|hook|query|migration|column|invariant)\b"
        r".*\b(is|was|will be)\b",
        re.I,
    ),
    re.compile(r"\b(verified|confirmed|tested|checked) that\b", re.I),
]
# Analytical-claim triggers — NEW (the §4a band: causal + already-implemented + inferred-dependency).
# NOTE: these feed scan_for_uncited_claims (the NEW citation detector) but NOT scan_for_unlabeled_claims
# (the back-compat SubagentStop shim, which iterates CODE_STRUCTURE_PATTERNS ONLY). The architecture/
# dependency claim-shape MUST live here, not in CODE_STRUCTURE_PATTERNS, so the SubagentStop refactor
# stays behavior-preserving (AC-1) — an earlier tuning pass had mis-placed it in CODE_STRUCTURE.
ANALYTICAL_CLAIM_PATTERNS = [
    re.compile(r"\b(because|due to|since|driven by|explained by|owing to)\b", re.I),
    re.compile(
        r"\b(already|redundant|no-?op|not needed|unnecessary|needs to be (?:added|implemented|built))\b",
        re.I,
    ),
    # Inferred-dependency / architecture claims: "the gate/floor/pipeline ... is/are/was" without a
    # citation. tuning corpus: +3 ticket-scope misses at 0 added FP on 15 realistic negatives. The CITATION
    # gate still applies (a coefficient/file:line in the +/-1 window escapes the flag).
    # FP-tuning (owner decision): (1) the subject→copula gap is `[^.\n]*`, NOT `.*` — it must stay
    # ONE clause, so "this ticket wants. Here it is" no longer matches across a sentence break; (2) dropped
    # the weak generic nouns `ticket`(singular)|`step`|`approach`|`fix` that fire on ordinary prose — no
    # positive case relies on them (one row needs `tickets` plural, kept). Tuning-corpus recall held 7/10, FP 0/15.
    re.compile(
        r"\b(the|this|these|that)\b[^.\n]*"
        r"\b(gate|floor|tickets|pipeline|machinery|estimator)\b[^.\n]*"
        r"\b(is|was|are|were|will be)\b",
        re.I,
    ),
]
QUANTIFIER_PATTERN = re.compile(
    # tuning note: bare `only|always|never|...` matches ~13% of real prose -> blocks most turns
    # in block mode. Require a CLAIM SHAPE (AC-4 "on a code/data quantity"); drop noisy only/can't.
    # (a) copula + (<=2 words) + quantifier: "users are never admins", "the cache is always warm"
    r"\b(?:is|are|was|were|remains?|stays?|will\s+be)\b(?:\s+\w+){0,2}\s+"
    r"\b(?:never|always|permanently|inherent(?:ly)?)\b"
    # (b) quantifier + predicate word (verb OR adjective): "never scalable", "never become
    #     scalable", "always fires". Verbatim miss-(c) was "never become scalable" -- branch (a)'s
    #     copula form alone misses it; a self-authored "are never" test hid this (found via review).
    #     A filler-stopword negative-lookahead excludes "never mind" / "always there" / "we never do"
    #     (found via review: bare `+\w+` over-flagged conversational prose in block mode).
    r"|\b(?:never|always|permanently)\b\s+"
    r"(?!(?:mind|there|the|this|that|a|an|so|just|more|again|too|very|only|yet|"
    r"really|quite|enough|was|is|are|were|do|did|does|said|gonna|going|here|now)\b)\w+",
    re.I,
)
LABEL_PATTERN = re.compile(r"\b(Verified|Estimated|Assumed|Unknown)\b")
# Citation token: file:line | coefficient-shaped value | backticked value/SQL | row count.
# tuning note: a BARE integer (date/count/version) matches ~37% of prose and would falsely
# satisfy the gate. Require a coefficient-SHAPED value (=, decimal, unit, or backtick), not any number.
CITATION_PATTERN = re.compile(
    r"(?:[\w./-]+\.[A-Za-z]\w*:\d+"  # file:line  (model_fit.py:123)
    r"|\b\w+\s*=\s*[-+]?\d+(?:\.\d+)?\b"  # assignment  (x=1, count=3)
    r"|(?<![vV])[-+]?\d+\.\d+"  # decimal value (1.5, 0.25); (?<![vV]) skips version strings like v5.1
    r"|\b\d+(?:\.\d+)?\s*(?:%|ms|kb|x)"  # number + unit  (70%, 150ms, 3x)
    r"|`[^`]*\b(?:SELECT|INSERT|UPDATE|FROM|WHERE)\b[^`]*`"  # backticked SQL
    r"|`[^`]*\d[^`]*`"  # backticked value with a digit
    r"|\b\d+\s+rows?\b)",  # row count  (19 rows)
    re.I,
)


@dataclass(frozen=True)
class Finding:
    line: str
    line_no: int
    blindspot_class: str
    why: str


def _behavioral_trigger(line: str) -> bool:
    return any(p.search(line) for p in CODE_STRUCTURE_PATTERNS) or any(
        p.search(line) for p in ANALYTICAL_CLAIM_PATTERNS
    )


def classify(line: str) -> str:
    """Best-effort blindspot-class label for a flagged line (AC-8 + reject render)."""
    if QUANTIFIER_PATTERN.search(line):
        return "snapshot-vs-permanent"
    if ANALYTICAL_CLAIM_PATTERNS[1].search(line):
        return "already-implemented"
    if ANALYTICAL_CLAIM_PATTERNS[2].search(line):
        return "inferred-dependency"
    if ANALYTICAL_CLAIM_PATTERNS[0].search(line):
        return "coefficient-vs-intuition"
    if CODE_STRUCTURE_PATTERNS[1].search(line):
        return "inferred-dependency"
    return "coefficient-vs-intuition"


def _window(lines: list[str], i: int) -> str:
    """True +/-1 line window (claim line + above + below)."""
    parts = [lines[i]]
    if i > 0:
        parts.append(lines[i - 1])
    if i + 1 < len(lines):
        parts.append(lines[i + 1])
    return " ".join(parts)


def scan_for_unlabeled_claims(text: str) -> list[str]:
    """BACK-COMPAT: code-structure claim lacking a confidence label (SubagentStop's original semantics)."""
    misses: list[str] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not any(p.search(line) for p in CODE_STRUCTURE_PATTERNS):
            continue
        window = line + " " + (lines[i - 1] if i > 0 else "")
        if LABEL_PATTERN.search(window):
            continue
        misses.append(line.strip())
    return misses


def scan_for_uncited_claims(text: str) -> list[Finding]:
    """AC-3: a behavioral claim (code-structure OR analytical) lacking a citation token in its +/-1 window."""
    findings: list[Finding] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not _behavioral_trigger(line):
            continue
        if CITATION_PATTERN.search(_window(lines, i)):
            continue
        findings.append(
            Finding(
                line.strip(),
                i + 1,
                classify(line),
                "behavioral claim, no citation token",
            )
        )
    return findings


def scan_for_quantifier_claims(text: str) -> list[Finding]:
    """AC-4: an absolute/temporal quantifier (snapshot-vs-permanent) — cite the rate of change."""
    findings: list[Finding] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if QUANTIFIER_PATTERN.search(line):
            findings.append(
                Finding(
                    line.strip(),
                    i + 1,
                    "snapshot-vs-permanent",
                    "absolute/temporal quantifier — is this time-varying? cite its rate of change",
                )
            )
    return findings
