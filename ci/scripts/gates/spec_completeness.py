from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Any

_SECTION_DEFS = {
    "endpoint_freeze": (
        "Endpoint Freeze",
        ["endpoint", "uri", "route", "method", "http", "api contract"],
        "Explicit HTTP method + URI for each endpoint. Required before test authoring.",
    ),
    "validation_precedence": (
        "Validation Precedence",
        ["validation precedence", "error precedence", "check order", "error order", "precedence table"],
        "Table ranking validation checks and status codes for mixed-invalid requests.",
    ),
    "confirmation_contract": (
        "Confirmation Input Contract",
        ["confirmation", "confirm", "confirmation contract", "confirmation input"],
        "Explicit outcomes for omitted, empty-string, and whitespace-only confirmation values.",
    ),
    "selection_policy": (
        "Selection Policy",
        ["selection policy", "random policy", "distribution policy", "weighting", "uniform", "weighted"],
        "Declaration of default selection policy (uniform/weighted) and deterministic test hook requirement.",
    ),
    "selector_mode": (
        "Selector Mode Contract",
        ["selector mode", "selector contract", "selection mode", "mixed selector"],
        "Allowed selector forms and mixed-selector rejection behavior.",
    ),
    "destructive_contract": (
        "Destructive Contract Freeze",
        ["destructive contract", "destructive freeze", "delete contract", "deletion contract", "destructive endpoint"],
        "Method+URI, required confirmation fields, and deterministic status-class outcomes for delete/destructive ops.",
    ),
    "deferred_boundary": (
        "Deferred Boundary Statement",
        ["deferred boundary", "deferred wiring", "cross-milestone", "future milestone", "deferred integration"],
        "Explicit statement of any cross-milestone wiring boundaries and what is out-of-scope for this ticket.",
    ),
    "failure_taxonomy": (
        "Failure Taxonomy",
        ["failure taxonomy", "error taxonomy", "status code map", "status taxonomy", "rejection taxonomy"],
        "Status-code taxonomy for validation errors (e.g. 400 vs 403 for different rejection classes).",
    ),
}

_TYPE_REQUIREMENTS: dict[str, list[str]] = {
    "generic": [],
    "api": [
        "endpoint_freeze",
        "validation_precedence",
        "failure_taxonomy",
    ],
    "destructive": [
        "endpoint_freeze",
        "destructive_contract",
        "confirmation_contract",
        "validation_precedence",
        "failure_taxonomy",
    ],
    "randomness": [
        "selection_policy",
    ],
    "load-open": [
        "endpoint_freeze",
        "selector_mode",
        "failure_taxonomy",
    ],
}

_HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)


def _extract_headings(text: str) -> list[str]:
    return [m.group(1).strip().lower() for m in _HEADING_RE.finditer(text)]


def _heading_matches(headings: list[str], aliases: list[str]) -> bool:
    for h in headings:
        for alias in aliases:
            if alias.lower() in h:
                return True
    return False


def _check(spec_path: Path, types: list[str]) -> list[tuple[str, str]]:
    text = spec_path.read_text()
    headings = _extract_headings(text)

    required_keys: set[str] = set()
    for t in types:
        t = t.strip().lower()
        if t not in _TYPE_REQUIREMENTS:
            print(f"WARNING: unknown ticket type '{t}'. Known: {', '.join(_TYPE_REQUIREMENTS)}", file=sys.stderr)
            return {
                "status": "FAIL",
                "message": f"Unknown ticket type: {t}",
                "violations": [
                    {
                        "file": str(spec_path),
                        "line": 0,
                        "rule": "unknown_ticket_type",
                        "message": f"Unrecognized ticket type: {t}",
                        "severity": "ERROR",
                    }
                ],
                "remediation_hints": [f"Use one of: {', '.join(_TYPE_REQUIREMENTS)}"],
            }
        required_keys.update(_TYPE_REQUIREMENTS[t])

    missing: list[tuple[str, str]] = []
    for key in sorted(required_keys):
        canonical, aliases, description = _SECTION_DEFS[key]
        if not _heading_matches(headings, aliases):
            missing.append((canonical, description))

    return missing


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    spec_file = inputs.get("spec_file")
    ticket_type = inputs.get("ticket_type", "generic")

    if not spec_file:
        return {
            "status": "FAIL",
            "message": "Missing required input: spec_file",
            "violations": [
                {
                    "file": "",
                    "line": 0,
                    "rule": "input_validation",
                    "message": "spec_file is required but was not provided.",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": ["Pass --input with a valid spec_file path."],
        }

    spec_path = Path(spec_file)
    if not spec_path.exists():
        return {
            "status": "FAIL",
            "message": f"Spec file not found: {spec_file}",
            "violations": [
                {
                    "file": str(spec_file),
                    "line": 0,
                    "rule": "file_exists",
                    "message": f"Spec file does not exist: {spec_file}",
                    "severity": "ERROR",
                }
            ],
            "remediation_hints": ["Provide a valid path to an existing spec file."],
        }

    types = [t.strip() for t in ticket_type.split(",")] if isinstance(ticket_type, str) else ["generic"]

    missing = _check(spec_path, types)

    if not missing:
        file_bytes = spec_path.read_bytes()
        return {
            "status": "PASS",
            "message": "All required sections present.",
            "artifacts": [
                {
                    "path": str(spec_path),
                    "sha256": hashlib.sha256(file_bytes).hexdigest(),
                    "size_bytes": len(file_bytes),
                }
            ],
        }

    violations = []
    remediation_hints = []
    for canonical, description in missing:
        violations.append(
            {
                "file": str(spec_path),
                "line": 0,
                "rule": canonical,
                "message": f"Missing section: {canonical} — {description}",
                "severity": "ERROR",
            }
        )
        remediation_hints.append(f"Add a ## {canonical} section to the spec.")

    return {
        "status": "FAIL",
        "message": f"{len(missing)} required section(s) missing.",
        "violations": violations,
        "remediation_hints": remediation_hints,
    }
