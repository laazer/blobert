#!/usr/bin/env python3
"""
Spec completeness checker with automatic type inference.

Validates that a spec .md file contains all required sections for its declared ticket type.
Designed to run between Spec Agent completion and TEST_DESIGN stage advance.

Usage:
    python ci/scripts/spec_completeness_check.py <spec_file.md> [--type TYPE] [--ticket TICKET_PATH]

    TYPE is one of: api, destructive, randomness, load-open, generic (default: inferred from ticket or generic)
    Multiple types can be comma-separated: --type destructive,api
    TICKET_PATH: path to ticket .md file for automatic type inference (optional; spec file can be inferred from ticket)

Exit codes:
    0  — all required sections present
    1  — one or more required sections missing
    2  — usage error

Section detection is fuzzy: matches headings that contain the required keywords,
case-insensitive, with common aliases tolerated.

Type inference (if --type not provided):
    - Contains "delete", "remove", "purge" → destructive
    - Contains "POST", "PUT", "PATCH", "endpoint", "HTTP method" → api
    - Contains "random", "uniform", "weighted", "seed", "distribution" → randomness
    - Contains "load existing", "open", "multiple selector", "selector form" → load-open
    - Otherwise → generic
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
# Type inference heuristics
# ---------------------------------------------------------------------------

def infer_type(text: str) -> str:
    """
    Infer ticket type from ticket description/scope.

    Returns one of: destructive, api, randomness, load-open, generic

    Strategy:
    - Destructive: contains "delete endpoint", "delete operation", "remove endpoint", "purge data"
    - API: contains "POST /", "PUT /", "PATCH /", "http method", "http request", "rest api"
    - Randomness: contains "random", "uniform", "weighted", "seed", "distribution policy"
    - Load-open: contains "load existing", "open", "multiple selector", "selector form"
    - Generic: default fallback

    Note: heuristics are deliberately conservative to avoid false positives.
    Explicit --type flag overrides inference.
    """
    text_lower = text.lower()

    # Destructive operations (context-specific to avoid false positives)
    destructive_patterns = [
        "delete endpoint",
        "delete operation",
        "delete api",
        "remove endpoint",
        "remove operation",
        "purge data",
        "drop table",
        "destroy record",
    ]
    if any(p in text_lower for p in destructive_patterns):
        return "destructive"

    # API/endpoint operations
    api_patterns = [
        "post /",
        "put /",
        "patch /",
        "http method",
        "http request",
        "http endpoint",
        "rest api",
    ]
    if any(p in text_lower for p in api_patterns):
        return "api"

    # Randomness/selection (specific keywords)
    randomness_patterns = [
        "random distribution",
        "uniform distribution",
        "weighted distribution",
        "seed behavior",
        "distribution policy",
        "probabilistic selection",
    ]
    if any(p in text_lower for p in randomness_patterns):
        return "randomness"

    # Load/open/selector operations
    load_open_patterns = [
        "load existing",
        "open file",
        "open scene",
        "multiple selector",
        "selector form",
        "selector mode",
        "mixed selector",
    ]
    if any(p in text_lower for p in load_open_patterns):
        return "load-open"

    # Default
    return "generic"


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
    ticket_file: Path | None = None
    types: list[str] | None = None
    inferred_type: str | None = None

    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            types = [t.strip() for t in args[i + 1].split(",")]
            i += 2
        elif args[i].startswith("--type="):
            types = [t.strip() for t in args[i].split("=", 1)[1].split(",")]
            i += 1
        elif args[i] == "--ticket" and i + 1 < len(args):
            ticket_file = Path(args[i + 1])
            i += 2
        elif args[i].startswith("--ticket="):
            ticket_file = Path(args[i].split("=", 1)[1])
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

    # If no --type provided, infer from ticket file or spec file
    if types is None:
        if ticket_file is not None:
            if not ticket_file.exists():
                print(f"WARNING: ticket file not found: {ticket_file}, inferring type from spec", file=sys.stderr)
            else:
                ticket_text = ticket_file.read_text()
                inferred_type = infer_type(ticket_text)
                types = [inferred_type]
        else:
            # Try to infer from spec file
            spec_text = spec_file.read_text()
            inferred_type = infer_type(spec_text)
            types = [inferred_type]

    if types is None:
        types = ["generic"]

    type_str = ", ".join(types)
    if inferred_type:
        print(f"spec-completeness-check: {spec_file.name}  type={type_str} (inferred)")
    else:
        print(f"spec-completeness-check: {spec_file.name}  type={type_str}")

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
