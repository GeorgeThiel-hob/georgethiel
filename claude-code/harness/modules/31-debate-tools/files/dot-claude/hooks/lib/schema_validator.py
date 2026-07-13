"""Schema validation gate for inter-agent structured output (module 31-debate-tools).

Standalone, generalized mini-JSON-schema validator — no `src/` import anywhere, so it
runs in any repo this kit is installed into. The validation ENGINE below
(`ValidationResult`, `_validate_field`, `_validate_object`, `validate`, `_main`) is
domain-agnostic; only the `_SCHEMAS` dict is specific to this module's two skills
(COUNCIL, DEBATE).

Usage (CLI):
    python3 .claude/hooks/lib/schema_validator.py --schema <name> --input '<json>'

Exit code 0 = valid, exit code 1 = invalid (errors written to stderr).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Schema definitions
#
# ADAPT: add or edit schemas here for your own debate-tools variants — this dict is the
# only project-specific surface in this file. `smac_agent` and `model_chat_delta` are
# unchanged from the schemas COUNCIL/DEBATE validate against; `debate_topic_classifier`
# replaces a pattern-source high-stakes-topic classifier schema (see
# docs/harness/31-debate-tools.md for the field-rename table).
# ---------------------------------------------------------------------------

_SCHEMAS: dict[str, list[dict[str, Any]]] = {
    "smac_agent": [
        {"name": "verdict", "type": "str", "required": True},
        {"name": "confidence", "type": "float", "required": True},
        {"name": "reasoning", "type": "str", "required": True},
        {"name": "unresolved_objections", "type": "list[str]", "required": True},
    ],
    "debate_topic_classifier": [
        {"name": "touches_high_stakes_logic", "type": "bool", "required": True},
        {"name": "schema_change", "type": "bool", "required": True},
        {"name": "multi_system_coordination", "type": "bool", "required": True},
        {"name": "irreversible_action_gated", "type": "bool", "required": True},
        {
            "name": "routing_decision",
            "type": "enum",
            "values": ["high_stakes_t3", "low_stakes"],
            "required": True,
        },
        {"name": "confidence", "type": "float", "required": True},
    ],
    "model_chat_delta": [
        {"name": "round", "type": "int", "required": True},
        {"name": "agent_id", "type": "str", "required": True},
        {"name": "position_delta", "type": "str", "required": False},
        {"name": "key_new_argument", "type": "str", "required": False},
        {"name": "concession", "type": "str", "required": False},
        {"name": "unresolved_objections", "type": "list[str]", "required": True},
        {"name": "framing_shift", "type": "bool", "required": True},
    ],
}

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_field(
    field_def: dict[str, Any],
    value: Any,
    prefix: str = "",
) -> list[str]:
    """Return a list of error strings for a single field value.

    An empty list means the field is valid.
    """
    errors: list[str] = []
    name = field_def["name"]
    qualified = f"{prefix}{name}" if prefix else name
    field_type = field_def["type"]

    # Null is allowed for optional (non-required) fields; reject null for required.
    if value is None:
        if field_def["required"]:
            errors.append(f"'{qualified}': required field is null")
        # Optional null is valid — no further type checks needed.
        return errors

    if field_type == "str":
        if not isinstance(value, str):
            errors.append(f"'{qualified}': expected str, got {type(value).__name__}")

    elif field_type == "int":
        # bool is a subclass of int in Python — reject bools for int fields.
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"'{qualified}': expected int, got {type(value).__name__}")

    elif field_type == "float":
        # bool is a subclass of int (and transitively float-compatible) — reject bools.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"'{qualified}': expected float, got {type(value).__name__}")

    elif field_type == "bool":
        if not isinstance(value, bool):
            errors.append(f"'{qualified}': expected bool, got {type(value).__name__}")

    elif field_type == "enum":
        allowed = field_def["values"]
        if value not in allowed:
            errors.append(
                f"'{qualified}': invalid enum value '{value}'; allowed: {allowed}"
            )

    elif field_type == "list[str]":
        if not isinstance(value, list):
            errors.append(f"'{qualified}': expected list, got {type(value).__name__}")
        else:
            for idx, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(
                        f"'{qualified}[{idx}]': expected str, got {type(item).__name__}"
                    )

    return errors


def _validate_object(
    data: dict[str, Any], schema_name: str, prefix: str = ""
) -> list[str]:
    """Validate a single dict against the named schema. Return list of errors."""
    if schema_name not in _SCHEMAS:
        raise ValueError(f"Unknown schema: '{schema_name}'")

    schema = _SCHEMAS[schema_name]
    errors: list[str] = []

    for field_def in schema:
        name = field_def["name"]
        qualified = f"{prefix}{name}" if prefix else name

        if name not in data:
            if field_def["required"]:
                errors.append(f"'{qualified}': required field is missing")
            # Optional field absent is fine — no further checks.
            continue

        errors.extend(_validate_field(field_def, data[name], prefix=prefix))

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate(data: dict[str, Any] | list[Any], schema_name: str) -> ValidationResult:
    """Validate *data* against *schema_name*.

    Accepts either a single JSON object (dict) or a JSON array (list). Arrays are
    validated element-by-element; any failing element marks the entire result as
    invalid.

    Raises:
        ValueError: if *schema_name* is not a known schema.
    """
    if schema_name not in _SCHEMAS:
        raise ValueError(f"Unknown schema: '{schema_name}'")

    if isinstance(data, list):
        all_errors: list[str] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                all_errors.append(
                    f"[{idx}]: expected object, got {type(item).__name__}"
                )
                continue
            element_errors = _validate_object(item, schema_name, prefix="")
            for err in element_errors:
                all_errors.append(f"[{idx}] {err}")
        return ValidationResult(valid=len(all_errors) == 0, errors=all_errors)

    if not isinstance(data, dict):
        return ValidationResult(
            valid=False,
            errors=[f"expected object, got {type(data).__name__}"],
        )

    errors = _validate_object(data, schema_name)
    return ValidationResult(valid=len(errors) == 0, errors=errors)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate JSON against a named inter-agent schema."
    )
    parser.add_argument(
        "--schema", required=True, help="Schema name to validate against"
    )
    parser.add_argument(
        "--input",
        required=True,
        dest="input_json",
        help="JSON string to validate",
    )
    args = parser.parse_args(argv)

    try:
        data = json.loads(args.input_json)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        result = validate(data, args.schema)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.valid:
        return 0

    for err in result.errors:
        print(err, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(_main())
