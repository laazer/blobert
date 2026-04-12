#!/usr/bin/env python3
"""
Spec completeness checker.

Validates that a spec .md file contains all required sections for its declared ticket type.
Designed to run between Spec Agent completion and TEST_DESIGN stage advance.

Usage:
    python ci/scripts/spec_completeness_check.py <spec_file.md> [--type TYPE]

    TYPE is one of: api, destructive, randomness, load-open, generic (default: generic)
    Multiple types can be comma-separated: --type destructive,api

Exit codes:
    0  — all required sections present
    1  — one or more required sections missing
    2  — usage error

Section detection is fuzzy: matches headings that contain the required keywords,
case-insensitive, with common aliases tolerated.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Required sections by ticket type
# ---------------------------------------------------------------------------

# Each entry: (canonical_name, [keyword_aliases], description_for_error)
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

# Required sections per ticket type
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


# ---------------------------------------------------------------------------
# Heading extraction
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)


def _extract_headings(text: str) -> list[str]:
    return [m.group(1).strip().lower() for m in _HEADING_RE.finditer(text)]


def _heading_matches(headings: list[str], aliases: list[str]) -> bool:
    for h in headings:
        for alias in aliases:
            if alias.lower() in h:
                return True
    return False


# ---------------------------------------------------------------------------
# Check
# ---------------------------------------------------------------------------

def check(spec_path: Path, types: list[str]) -> list[tuple[str, str]]:
    """
    Returns list of (section_canonical_name, description) for missing required sections.
    Empty list = all present.
    """
    text = spec_path.read_text()
    headings = _extract_headings(text)

    required_keys: set[str] = set()
    for t in types:
        t = t.strip().lower()
        if t not in _TYPE_REQUIREMENTS:
            print(f"WARNING: unknown ticket type '{t}'. Known: {', '.join(_TYPE_REQUIREMENTS)}", file=sys.stderr)
        required_keys.update(_TYPE_REQUIREMENTS.get(t, []))

    missing: list[tuple[str, str]] = []
    for key in sorted(required_keys):
        canonical, aliases, description = _SECTION_DEFS[key]
        if not _heading_matches(headings, aliases):
            missing.append((canonical, description))

    return missing


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2

    spec_file: Path | None = None
    types: list[str] = ["generic"]

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            types = [t.strip() for t in args[i + 1].split(",")]
            i += 2
        elif args[i].startswith("--type="):
            types = [t.strip() for t in args[i].split("=", 1)[1].split(",")]
            i += 1
        elif not args[i].startswith("--"):
            spec_file = Path(args[i])
            i += 1
        else:
            print(f"Unknown argument: {args[i]}", file=sys.stderr)
            return 2

    if spec_file is None:
        print("ERROR: spec file path required.", file=sys.stderr)
        return 2

    if not spec_file.exists():
        print(f"ERROR: spec file not found: {spec_file}", file=sys.stderr)
        return 2

    print(f"spec-completeness-check: {spec_file.name}  type={', '.join(types)}")

    missing = check(spec_file, types)

    if not missing:
        print("PASS: all required sections present.")
        return 0

    print(f"\nFAIL: {len(missing)} required section(s) missing:\n")
    for canonical, description in missing:
        print(f"  MISSING: ## {canonical}")
        print(f"           {description}\n")

    print("Add the missing sections to the spec before advancing to TEST_DESIGN.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
