#!/usr/bin/env python3
"""
Token budget analyzer — Forecast token consumption per ticket.

Estimates tokens needed for each TDD stage based on ticket complexity heuristics.
Used by autopilot pre-flight check to warn about budget insufficiency.

Usage:
    python ci/scripts/token_budget_analyzer.py <ticket.md> [--remaining-budget N] [--json]

Exit codes:
    0 — analysis complete (check JSON for actual status)
    1 — ticket not found or parse error
    2 — usage error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Complexity scoring
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def extract_acceptance_criteria(text: str) -> list[str]:
    """Extract acceptance criteria from ticket markdown."""
    lines = text.split('\n')
    criteria = []
    in_ac_section = False

    for line in lines:
        if '# Acceptance Criteria' in line or '## Acceptance Criteria' in line:
            in_ac_section = True
            continue
        if in_ac_section and line.startswith('# '):
            break  # End of AC section
        if in_ac_section and line.startswith('- '):
            criteria.append(line)

    return criteria


def extract_dependencies(text: str) -> list[str]:
    """Extract dependencies from ticket markdown."""
    lines = text.split('\n')
    deps = []
    in_dep_section = False

    for line in lines:
        if '# Dependencies' in line or '## Dependencies' in line:
            in_dep_section = True
            continue
        if in_dep_section and line.startswith('# '):
            break
        if in_dep_section and line.strip() and not line.startswith('##'):
            # Skip "None" or empty sections
            if line.strip() not in ('None', 'None.'):
                deps.append(line.strip())

    return [d for d in deps if d]  # Filter empty strings


def infer_subsystems(text: str) -> list[str]:
    """Infer which subsystems the ticket touches."""
    text_lower = text.lower()
    subsystems = []

    if any(w in text_lower for w in ['godot', 'gd script', 'scene', '.gd', 'script/']):
        subsystems.append('godot')
    if any(w in text_lower for w in ['python', 'asset_generation/python', 'blender', '.py', 'pyproject']):
        subsystems.append('python')
    if any(w in text_lower for w in ['web', 'fastapi', 'frontend', 'react', 'npm', 'typescript']):
        subsystems.append('web')
    if any(w in text_lower for w in ['gate', 'validation', 'enforcement', 'audit', 'governance']):
        subsystems.append('infrastructure')

    return subsystems


def score_complexity(ticket_path: Path) -> int:
    """
    Score ticket complexity (1-5, where 5 is most complex).

    Scoring rules:
    - Base: 2
    - +1 for each: description >500 chars, >5 ACs, >3 deps, Godot subsystem, complex gate
    - Cap at 5
    """
    text = ticket_path.read_text()
    score = 2  # Base

    # Heuristic 1: Description length
    if len(text) > 500:
        score += 1

    # Heuristic 2: Acceptance criteria count
    acs = extract_acceptance_criteria(text)
    if len(acs) > 5:
        score += 1

    # Heuristic 3: Dependencies
    deps = extract_dependencies(text)
    if len(deps) > 3:
        score += 1

    # Heuristic 4: Subsystems
    subsystems = infer_subsystems(text)
    if 'godot' in subsystems:
        score += 1
    if 'infrastructure' in subsystems or 'web' in subsystems:
        score += 1

    # Cap at 5
    return min(score, 5)


# ---------------------------------------------------------------------------
# Stage estimates
# ---------------------------------------------------------------------------

@dataclass
class StageEstimate:
    """Token estimate for a single stage."""
    stage: str
    base_cost: int  # in thousands
    multiplier: float  # complexity factor
    estimated_tokens: int  # final estimate in thousands

    def __init__(self, stage: str, base_cost: int, multiplier: float, complexity: int):
        self.stage = stage
        self.base_cost = base_cost
        self.multiplier = multiplier
        self.estimated_tokens = int(base_cost * (complexity * multiplier))


def estimate_stages(complexity: int) -> dict[str, int]:
    """
    Estimate token consumption per stage.

    Returns dict of {stage: tokens_in_thousands}
    """
    stages = [
        ('PLANNING', 12, 0.8),
        ('SPECIFICATION', 20, 1.2),
        ('TEST_DESIGN', 30, 1.3),
        ('TEST_BREAK', 15, 1.2),
        ('IMPLEMENTATION', 50, 1.5),
        ('ACCEPTANCE', 10, 0.7),
        ('LEARNING', 5, 0.0),  # Fixed 5k, not multiplied
    ]

    estimates = {}
    for stage, base, mult in stages:
        if mult == 0.0:
            # Fixed cost (LEARNING)
            estimates[stage] = 5
        else:
            estimates[stage] = int(base * (complexity * mult))

    return estimates


# ---------------------------------------------------------------------------
# Budget check
# ---------------------------------------------------------------------------

def check_budget(total_estimate: int, remaining_budget: int) -> dict:
    """
    Determine budget sufficiency and recommendations.

    Returns dict with:
    - can_complete: bool
    - confidence: str (low/medium/high)
    - recommendations: list[str]
    """
    if total_estimate <= remaining_budget:
        margin_pct = int(100 * (remaining_budget - total_estimate) / total_estimate)
        if margin_pct >= 30:
            return {
                'can_complete': True,
                'confidence': 'high',
                'margin_percent': margin_pct,
                'recommendations': [
                    'Budget is sufficient for full TDD cycle',
                ]
            }
        elif margin_pct >= 10:
            return {
                'can_complete': True,
                'confidence': 'medium',
                'margin_percent': margin_pct,
                'recommendations': [
                    'Budget is tight; monitor token usage during SPECIFICATION and IMPLEMENTATION stages',
                    'Consider enabling lean mode (skip LEARNING) if needed',
                ]
            }
        else:
            return {
                'can_complete': True,
                'confidence': 'low',
                'margin_percent': margin_pct,
                'recommendations': [
                    'Very tight budget; recommend splitting into multiple sessions',
                    'Suggestion: handle PLANNING + SPECIFICATION in session 1, TEST + IMPLEMENTATION in session 2',
                ]
            }
    else:
        shortfall = total_estimate - remaining_budget
        return {
            'can_complete': False,
            'confidence': 'low',
            'shortfall_tokens': shortfall,
            'recommendations': [
                f'Budget insufficient by {shortfall}k tokens',
                'Recommendation: defer ticket or use lean mode (skip LEARNING)',
                'Alternative: split implementation across two sessions',
            ]
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def analyze(ticket_path: Path, remaining_budget: int = 200000) -> dict:
    """
    Analyze ticket and return budget forecast.

    Args:
        ticket_path: Path to ticket .md file
        remaining_budget: Current token budget (default: 200k)

    Returns:
        dict with analysis results
    """
    if not ticket_path.exists():
        raise FileNotFoundError(f"Ticket not found: {ticket_path}")

    text = ticket_path.read_text()

    # Extract ticket ID
    lines = text.split('\n')
    ticket_id = "UNKNOWN"
    title = "Untitled"
    for line in lines[:20]:
        if line.startswith('# ') and not line.startswith('# Acceptance'):
            title = line[2:].strip()
        if line.startswith('Ticket:'):
            # Checkpoint header format: Ticket: `path/to/ticket.md`
            ticket_id = ticket_path.stem

    # Score complexity
    complexity = score_complexity(ticket_path)

    # Estimate stages
    stage_estimates = estimate_stages(complexity)
    total_estimate = sum(stage_estimates.values())

    # Check budget (convert remaining_budget from tokens to thousands)
    budget_check = check_budget(total_estimate, remaining_budget // 1000)

    return {
        'ticket_id': ticket_id,
        'title': title,
        'ticket_path': str(ticket_path),
        'complexity_score': complexity,
        'complexity_description': ['trivial', 'simple', 'medium', 'complex', 'very complex', 'extremely complex'][complexity],
        'stage_estimates': {k: f"{v}k" for k, v in stage_estimates.items()},
        'stage_estimates_tokens': stage_estimates,
        'total_estimate': f"{total_estimate}k",
        'total_estimate_tokens': total_estimate,
        'remaining_budget': f"{remaining_budget // 1000}k",
        'remaining_budget_tokens': remaining_budget,
        'remaining_after_ticket': f"{(remaining_budget - total_estimate * 1000) // 1000}k",
        'remaining_after_ticket_tokens': remaining_budget - total_estimate * 1000,
        **budget_check,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description='Estimate token budget for a ticket',
        usage='python ci/scripts/token_budget_analyzer.py <ticket.md> [--remaining-budget N] [--json]'
    )
    parser.add_argument('ticket', type=Path, help='Path to ticket .md file')
    parser.add_argument('--remaining-budget', type=int, default=200000, help='Current token budget (default: 200000)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    try:
        args = parser.parse_args()
    except SystemExit:
        return 2

    try:
        result = analyze(args.ticket, args.remaining_budget)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"\n📊 Token Budget Analysis\n")
        print(f"Ticket:     {result['ticket_id']} — {result['title']}")
        print(f"Complexity: {result['complexity_score']}/5 ({result['complexity_description']})")
        print(f"\nStage Estimates:")
        for stage, estimate in result['stage_estimates'].items():
            print(f"  {stage:20s} {estimate:>6s}")
        print(f"\nTotal Estimate:       {result['total_estimate']}")
        print(f"Remaining Budget:     {result['remaining_budget']}")
        print(f"After Ticket:         {result['remaining_after_ticket']}")
        print(f"\nBudget Status:        ", end='')
        if result['can_complete']:
            confidence = result['confidence'].upper()
            margin = result.get('margin_percent', 0)
            print(f"✓ CAN COMPLETE ({confidence}, +{margin}% margin)")
        else:
            shortfall = result.get('shortfall_tokens', 0)
            print(f"✗ INSUFFICIENT (short by {shortfall}k)")

        if result['recommendations']:
            print(f"\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
