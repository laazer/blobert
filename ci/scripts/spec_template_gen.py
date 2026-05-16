#!/usr/bin/env python3
"""
Spec template generator — Create skeleton spec document from ticket type.

Generates a populated spec file based on ticket type (api, destructive, randomness, governance, etc.)
with placeholder sections and examples.

Usage:
    python ci/scripts/spec_template_gen.py <ticket.md> --type <type> [--output <spec.md>]

    TYPE: api | destructive | randomness | governance | infrastructure | generic

Exit codes:
    0 — spec template generated successfully
    1 — ticket not found or parse error
    2 — usage error
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime


SPEC_TEMPLATES = {
    "api": """# Specification: {title}

**Ticket ID:** {ticket_id}
**Ticket Path:** {ticket_path}
**Spec Version:** 1.0
**Status:** DRAFT
**Last Updated:** {timestamp} by Spec Agent

---

## Functional Requirements

### Requirement 1: Endpoint Definition
- **AC Traceability:** AC-01
- **HTTP Method:** POST / GET / PUT / PATCH / DELETE
- **URI:** /api/v1/{resource}
- **Request Body:** JSON with fields [insert fields]
- **Response Body:** JSON with fields [insert fields]
- **Status Codes:**
  - 200: Success
  - 400: Validation error (invalid input)
  - 401: Unauthorized (missing token)
  - 404: Resource not found
  - 500: Server error

### Requirement 2: Input Validation
- **AC Traceability:** AC-02
- **Validation Order:** [see Validation Precedence section]
- **Error Response Format:** JSON with `{{error: string, code: string}}`

---

## Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Determinism** | Same input → same output |
| **Performance** | <200ms p99 latency |
| **Usability** | Clear error messages; no cryptic codes |

---

## Failure Modes & Error Handling

### Failure 1: Invalid Request Body
- **Detection:** JSON parse fails or required field missing
- **Error Message:** `{{"error": "missing required field 'name'", "code": "INVALID_INPUT"}}`
- **Recovery:** Client retries with corrected payload

### Failure 2: Resource Not Found
- **Detection:** Resource ID does not exist in database
- **Error Message:** `{{"error": "resource not found", "code": "NOT_FOUND"}}`
- **Recovery:** Client requests list endpoint to find valid ID

---

## Validation Precedence

| Check Order | Validation | Status Code |
|---|---|---|
| 1 | JSON parse valid | 400 |
| 2 | Required fields present | 400 |
| 3 | Field types correct | 400 |
| 4 | Field values in allowed range | 400 |
| 5 | Resource exists | 404 |
| 6 | User has permission | 401 |

---

## Deferred Scope

### Deferred to M903
- Rate limiting / throttling
- Request logging / audit trail
- Advanced query filtering
""",

    "destructive": """# Specification: {title}

**Ticket ID:** {ticket_id}
**Spec Version:** 1.0

---

## Functional Requirements

### Requirement 1: Delete Endpoint
- **AC Traceability:** AC-01
- **HTTP Method:** DELETE
- **URI:** /api/v1/{{resource}}/{{id}}
- **Confirmation Required:** Yes
- **Required Fields:** `confirmation_text: "DELETE"` (exact match)

### Requirement 2: Delete Confirmation Contract
- **Omitted Confirmation:** Return 400 "confirmation_text required"
- **Empty String Confirmation:** Return 400 "confirmation_text cannot be empty"
- **Wrong Confirmation:** Return 400 "confirmation_text must be 'DELETE'"
- **Correct Confirmation:** Proceed with deletion

---

## Failure Modes & Error Handling

### Failure 1: Missing Confirmation
- **Detection:** `confirmation_text` field not in request
- **Error Message:** `{{"error": "missing required field 'confirmation_text'", "code": "MISSING_CONFIRMATION"}}`
- **Status Code:** 400
- **Recovery:** Client includes confirmation field

### Failure 2: Wrong Confirmation Text
- **Detection:** `confirmation_text` != "DELETE"
- **Error Message:** `{{"error": "confirmation_text must be 'DELETE'", "code": "INVALID_CONFIRMATION"}}`
- **Status Code:** 400
- **Recovery:** Client sends correct confirmation text

---

## Destructive Contract Freeze

- **Endpoint:** DELETE /api/v1/{{resource}}/{{id}}
- **Confirmation Field:** `confirmation_text: "DELETE"` (case-sensitive, exact match)
- **Success:** Resource deleted; return 204 No Content
- **Failure:** See Failure Modes above; return 400 with error
- **Audit:** Log deletion with timestamp, user ID, resource ID
""",

    "governance": """# Specification: {title}

**Ticket ID:** {ticket_id}
**Spec Version:** 1.0

---

## Functional Requirements

### Requirement 1: Rule Definition
- **AC Traceability:** AC-01
- **Rule ID:** {{prefix}}-{{number}} (e.g., GV-001)
- **Rule Name:** Short descriptive name
- **Rule Description:** What violation is detected
- **Severity:** INFO | WARN | ERROR
- **Applicable To:** Godot | Python | TypeScript | All

### Requirement 2: Rule Enforcement
- **Check:** How rule is detected (linter, pattern matching, etc.)
- **Action:** WARN (informational) | BLOCK (fails gate)
- **Remediation:** Steps to fix violations
- **Configuration:** Tunable parameters (if any)

---

## Governance Rules Catalog

| Rule ID | Name | Severity | Scope | Enforcement |
|---|---|---|---|---|
| GV-001 | Bypass detection | ERROR | All | BLOCK |
| GV-002 | [Insert rule] | WARN | Python | WARN |
| ... | ... | ... | ... | ... |

---

## Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Determinism** | Same code → same violations |
| **False Positives** | <5% on benign command suite |
| **Performance** | <100ms per command inspection |

---

## Deferred Scope

### Deferred to M903
- Owner-based rule enforcement (who can override)
- Automated remediation
- Real-time violation dashboard
""",

    "infrastructure": """# Specification: {title}

**Ticket ID:** {ticket_id}
**Spec Version:** 1.0

---

## Functional Requirements

### Requirement 1: Core Mechanism
- **AC Traceability:** AC-01
- **Inputs:** [describe inputs]
- **Outputs:** [describe outputs]
- **Behavior:** [step-by-step algorithm or workflow]

### Requirement 2: Integration Point
- **Invocation:** How is this mechanism called?
- **Dependencies:** What must be in place first?
- **Exit Codes:** 0 (success), 1 (error), etc.

---

## Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Determinism** | Same input → same output |
| **Performance** | [Specific SLA, e.g., <5s on large repos] |
| **Maintainability** | Modular; <400 lines per component |

---

## Failure Modes & Error Handling

### Failure 1: [Insert failure mode]
- **Detection:** [How is failure detected?]
- **Error Message:** [User-facing message]
- **Recovery:** [How does user/system recover?]

---

## Deferred Scope

### Deferred to M903
- [Deferred feature 1]
- [Deferred feature 2]
""",

    "generic": """# Specification: {title}

**Ticket ID:** {ticket_id}
**Spec Version:** 1.0
**Status:** DRAFT

---

## Functional Requirements

### Requirement 1: [Feature Name]
- **AC Traceability:** AC-01, AC-02
- **Inputs:** [describe inputs]
- **Outputs:** [describe outputs]
- **Behavior:** [observable behavior]

---

## Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Determinism** | Same input → same output |
| **Performance** | [Performance targets] |

---

## Failure Modes

### Failure 1: [Insert failure mode]
- **Detection:** [How detected]
- **Error Message:** [User message]
- **Recovery:** [Resolution steps]

---

## Deferred Scope

### Deferred to M903
- [Deferred features]
""",
}


def extract_title(ticket_path: Path) -> str:
    """Extract ticket title from ticket markdown."""
    text = ticket_path.read_text()
    for line in text.split('\n'):
        if line.startswith('# ') and 'Title' in line:
            continue
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"


def extract_ticket_id(ticket_path: Path) -> str:
    """Extract ticket ID from path."""
    filename = ticket_path.stem
    if filename[0].isdigit():
        # Format: NN_slug → M902-N
        num_str = filename.split('_')[0].lstrip('0') or '0'
        # Infer milestone from parent path
        parent = str(ticket_path.parent)
        if '902_' in parent:
            return f"M902-{num_str}"
        return f"T-{num_str}"
    return filename


def generate_spec(ticket_path: Path, spec_type: str, output_path: Path | None = None) -> str:
    """
    Generate spec template and return content.

    Args:
        ticket_path: Path to ticket .md file
        spec_type: Type of ticket (api, destructive, governance, etc.)
        output_path: Optional path to write spec file

    Returns:
        Generated spec content
    """
    if not ticket_path.exists():
        raise FileNotFoundError(f"Ticket not found: {ticket_path}")

    template = SPEC_TEMPLATES.get(spec_type, SPEC_TEMPLATES["generic"])

    title = extract_title(ticket_path)
    ticket_id = extract_ticket_id(ticket_path)
    timestamp = datetime.now().isoformat(timespec='seconds')

    spec_content = template.format(
        title=title,
        ticket_id=ticket_id,
        ticket_path=str(ticket_path),
        timestamp=timestamp,
    )

    if output_path:
        output_path.write_text(spec_content)

    return spec_content


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description='Generate spec template from ticket')
    parser.add_argument('ticket', type=Path, help='Path to ticket .md file')
    parser.add_argument('--type', required=True, choices=list(SPEC_TEMPLATES.keys()), help='Ticket type')
    parser.add_argument('--output', type=Path, help='Output spec file path (optional; prints to stdout if omitted)')

    try:
        args = parser.parse_args()
    except SystemExit:
        return 2

    try:
        content = generate_spec(args.ticket, args.type, args.output)
        if args.output:
            print(f"✓ Spec template generated: {args.output}")
        else:
            print(content)
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
