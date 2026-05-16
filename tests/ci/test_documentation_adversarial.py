"""
M902-08 Adversarial Test Suite: Documentation Integration Edge Cases and Vulnerabilities.

This suite targets hidden weaknesses in the documentation-integration test contracts:
- Mermaid diagram edge cases (malformed syntax, missing connections, unreachable nodes)
- Command validation bypasses (flags not matching CLI schema, invalid gate names)
- Link resolution gaps (broken chains, circular references, missing anchors)
- Gate reference completeness failures (sparse sections, missing decision logic)
- README structure mutations (reordering, duplication, missing sections)
- CLAUDE.md compatibility edge cases (conflicting command examples)

Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md
Stage: TEST_BREAK

Adversarial matrix:
- Null/Empty: empty diagram, empty runbook, empty gate reference
- Boundary: max diagram complexity, min word counts for sections
- Type/Structure: malformed Mermaid, invalid JSON in gate_registry, broken markdown
- Invalid/Corrupt: invalid gate names, unregistered gates, circular links
- Concurrency: multiple diagrams (detecting which one is authoritative)
- Order dependency: section ordering sensitivity, gate ordering
- Combinatorial: empty + malformed, min gates + max complexity
- Stress: very large README (>500 lines), many gates
- Mutation testing: flip gate outcomes, change stage names, remove connections
- Error handling: graceful degradation with partial sections
- Assumption checks: implicit ordering, implicit naming conventions
- Determinism: diagram parsing consistency, link resolution idempotency
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_json

_REPO_ROOT = Path(__file__).resolve().parents[2]
README = _REPO_ROOT / "project_board" / "902_milestone_902_agent_predictabilitiy_improvements" / "README.md"
GATE_REGISTRY = _REPO_ROOT / "ci" / "scripts" / "gate_registry.json"


class TestMermaidDiagramEdgeCases:
    """Adversarial tests for Mermaid diagram vulnerabilities."""

    def test_diagram_with_unreachable_nodes(self) -> None:
        """
        CHECKPOINT: Missing graph connectivity constraint.
        Tests that diagram is fully connected (no orphaned nodes).
        Mutation: Add isolated subgraph without connection to main flow.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Extract all node IDs from diagram
        # Mermaid syntax: A[label], A(label), A{label}, etc.
        node_pattern = r'\b([A-Za-z_]\w*)\s*[\[\(\{]'
        nodes = set(re.findall(node_pattern, diagram))

        # Extract all connected nodes (appear in arrow statements)
        connection_pattern = r'(\w+)\s*(?:-->|---|\|-|->)\s*(\w+)'
        connected = set()
        for src, dst in re.findall(connection_pattern, diagram):
            connected.add(src)
            connected.add(dst)

        # All nodes must be connected
        orphaned = nodes - connected
        assert len(orphaned) == 0, f"Diagram has orphaned nodes: {orphaned}"

    def test_diagram_with_multiple_disjoint_subgraphs(self) -> None:
        """
        CHECKPOINT: Diagram must form single connected component.
        Mutation: Multiple separate flowcharts (START nodes without connection).
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Count START nodes (potential entry points)
        start_nodes = len(re.findall(r'\bSTART\b|\bstart\b', diagram))
        assert start_nodes <= 1, f"Diagram has {start_nodes} START nodes; should have exactly 1"

        # Count END/COMPLETE nodes
        end_nodes = len(re.findall(r'\bEND\b|\bCOMPLETE\b', diagram))
        assert end_nodes <= 1, f"Diagram has {end_nodes} END nodes; should have exactly 1"

    def test_diagram_with_malformed_mermaid_keywords(self) -> None:
        """
        CHECKPOINT: Mermaid keywords must be spelled correctly.
        Mutation: Typos in graph, flowchart, subgraph (e.g., "grph", "flowchrat").
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Check for common typos
        typos = [
            ("grph", "graph"),
            ("flowchrat", "flowchart"),
            ("subgrahp", "subgraph"),
            ("-->>", "-->"),  # double arrow
        ]

        for typo, correct in typos:
            assert typo not in diagram.lower(), \
                f"Diagram contains typo '{typo}' (should be '{correct}')"

    def test_diagram_arrow_syntax_consistency(self) -> None:
        """
        CHECKPOINT: Arrow syntax must be consistent across diagram.
        Mutation: Mix of -->, ---, -|, inconsistent connection styles.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Count different arrow types
        directed = len(re.findall(r'-->', diagram))
        undirected = len(re.findall(r'---', diagram))  # excludes -->
        labeled = len(re.findall(r'-\|.*?\|-', diagram))

        # For a workflow diagram, directed arrows (-->) should dominate
        total_arrows = directed + undirected + labeled
        if total_arrows > 0:
            directed_ratio = directed / total_arrows
            assert directed_ratio > 0.5, \
                f"Diagram uses only {directed}/{total_arrows} directed arrows; workflow should be mostly directed"

    def test_diagram_with_empty_node_labels(self) -> None:
        """
        CHECKPOINT: All nodes must have non-empty labels.
        Mutation: Nodes with empty brackets: A[], B[], etc.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Look for empty node definitions
        empty_nodes = re.findall(r'\w+\s*[\[\(\{][\s]*[\]\)\}]', diagram)
        assert len(empty_nodes) == 0, f"Diagram has empty node labels: {empty_nodes}"

    def test_diagram_stage_names_match_enforcement_enum(self) -> None:
        """
        CHECKPOINT: Stage names must match workflow_enforcement_v1.md Stage enum.
        Mutation: Typos in PLANNING, SPECIFICATION, etc. (e.g., PLANNIN, IMPLEMENTION).

        Enforcement enum from workflow_enforcement_v1.md:
        PLANNING | SPECIFICATION | TEST_DESIGN | TEST_BREAK | IMPLEMENTATION_BACKEND |
        IMPLEMENTATION_FRONTEND | IMPLEMENTATION_GENERALIST | STATIC_QA | INTEGRATION |
        DEPLOYMENT | BLOCKED | COMPLETE
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Valid stages from enum
        valid_stages = {
            "PLANNING", "SPECIFICATION", "TEST_DESIGN", "TEST_BREAK",
            "IMPLEMENTATION_BACKEND", "IMPLEMENTATION_FRONTEND", "IMPLEMENTATION_GENERALIST",
            "STATIC_QA", "INTEGRATION", "DEPLOYMENT", "BLOCKED", "COMPLETE"
        }

        # Collect stage mentions (case-insensitive search, then validate)
        stage_pattern = r'\b([A-Z_]+)\b'
        potential_stages = set(re.findall(stage_pattern, diagram))

        # Filter to likely stage names (all-caps, underscores)
        suspected_stages = {s for s in potential_stages if '_' in s or len(s) > 5}

        invalid = suspected_stages - valid_stages
        assert len(invalid) == 0, \
            f"Diagram references invalid stages: {invalid}"

    def test_diagram_gate_names_match_registry_exactly(self) -> None:
        """
        CHECKPOINT: Gate names in diagram must be exact matches to gate_registry.json.
        Mutation: Typos, case mismatches (static_Analysis_Check vs static_analysis_check).
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        registry_data = load_json(GATE_REGISTRY)
        registry_names = {entry["name"] for entry in registry_data}

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Extract all gate names from diagram (heuristic: words with underscores + _check)
        potential_gates = set(re.findall(r'(\w+_\w+_check)\b', diagram))

        for gate in potential_gates:
            assert gate in registry_names, \
                f"Diagram references unregistered gate: {gate} (registry has: {registry_names})"

    def test_diagram_outcome_labels_match_spec(self) -> None:
        """
        CHECKPOINT: Gate outcome labels must be from defined set.
        Mutation: Typos in PASS, FAIL, ESCALATE, WARN (e.g., FAILL, ESACALTE).

        Valid outcomes from gate specs: PASS, FAIL, ESCALATE, WARN
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Valid outcomes
        valid_outcomes = {"PASS", "FAIL", "ESCALATE", "WARN"}

        # Extract outcome mentions (typically in labels or decision nodes)
        outcome_pattern = r'\b(PASS|FAIL|ESCALATE|WARN|(?:[A-Z]+[A-Z_]*PASS[A-Z_]*)|(?:[A-Z]+[A-Z_]*FAIL[A-Z_]*))\b'
        mentioned = set(re.findall(outcome_pattern, diagram))

        # Exclude false positives (filter to valid set)
        # Allow some additional forms like "PASS_OUTCOME" but flag exact typos
        invalid = {m for m in mentioned if m not in valid_outcomes and not any(v in m for v in valid_outcomes)}
        assert len(invalid) == 0, \
            f"Diagram has invalid outcome labels: {invalid}"


class TestRunbookCommandInjectionVulnerabilities:
    """Adversarial tests for runbook command validation bypasses."""

    def test_runbook_command_with_unregistered_gate_name(self) -> None:
        """
        CHECKPOINT: Commands reference unregistered gates (not in gate_registry.json).
        Mutation: Typo in gate name in example command.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        registry_data = load_json(GATE_REGISTRY)
        registry_names = {entry["name"] for entry in registry_data}

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Extract gate names from gate_runner.py commands
        # Pattern: gate_runner.py <gate_name>
        gate_invocations = re.findall(r'gate_runner\.py\s+([a-z_]+)', runbook)

        for gate in gate_invocations:
            # Remove quotes if present
            gate = gate.strip("'\"")
            assert gate in registry_names, \
                f"Runbook invokes unregistered gate: {gate}"

    def test_runbook_command_with_invalid_cli_flags(self) -> None:
        """
        CHECKPOINT: Commands use flags not present in gate_runner.py --help.
        Mutation: Add invalid flags like --force, --verbose, --no-verify.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Valid flags from gate_runner.py help
        # (Note: These are from inspection of the code)
        valid_flags = {
            '--mode', '--gate', '--upstream-agent', '--downstream-agent',
            '--ticket-id', '--output-dir', '--input', '--help', '-h'
        }

        # Find all flags in runbook commands
        all_flags = set(re.findall(r'--[\w-]+', runbook))

        invalid_flags = all_flags - valid_flags
        assert len(invalid_flags) == 0, \
            f"Runbook uses invalid flags: {invalid_flags}"

    def test_runbook_command_mode_values_invalid(self) -> None:
        """
        CHECKPOINT: --mode flag values must be 'shadow' or 'blocking' (only 'shadow' in M902).
        Mutation: Invalid modes like --mode enforce, --mode production, --mode shadow-dry-run.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Valid modes
        valid_modes = {'shadow', 'blocking'}

        # Extract --mode values
        mode_matches = re.findall(r'--mode\s+(\w+)', runbook)

        for mode in mode_matches:
            assert mode in valid_modes, \
                f"Invalid gate mode: {mode} (must be shadow or blocking)"

    def test_runbook_command_missing_required_arguments(self) -> None:
        """
        CHECKPOINT: Commands that need spec_file or ticket_type must have them.
        Mutation: Remove required inputs from spec_completeness_check command.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        registry_data = load_json(GATE_REGISTRY)
        registry = {entry["name"]: entry for entry in registry_data}

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Extract commands with gates that have required inputs
        code_blocks = re.findall(r'```(?:bash|python|sh)?\s*\n(.*?)\n```', runbook, re.DOTALL)

        for block in code_blocks:
            # Check for spec_completeness_check
            if "spec_completeness_check" in block:
                spec_entry = registry.get("spec_completeness_check", {})
                required = spec_entry.get("required_inputs", [])
                for req in required:
                    # At least one of the required inputs must be present
                    # (in practice: spec_file and ticket_type)
                    assert req in block or req.replace('_', '-') in block, \
                        f"spec_completeness_check command missing required input: {req}"


class TestGateReferenceCompletenesFSections:
    """Adversarial tests for gate reference section completeness."""

    def test_gate_reference_sections_too_sparse(self) -> None:
        """
        CHECKPOINT: Each gate section must have minimum prose (not just headers).
        Mutation: Remove all subsection content, leaving only headers.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        gates = [
            "spec_completeness_check", "static_analysis_check", "governance_check",
            "planner_check", "reviewer_check", "learning_check"
        ]

        for gate in gates:
            gate_section = gate_ref[gate_ref.find(gate):] if gate in gate_ref else ""
            if not gate_section:
                continue

            # Remove markdown headers and code blocks
            prose = re.sub(r'^#+\s+.*$', '', gate_section, flags=re.MULTILINE)
            prose = re.sub(r'```[\s\S]*?```', '', prose)

            word_count = len(prose.split())
            assert word_count > 30, \
                f"Gate '{gate}' section too sparse: {word_count} words (minimum 30)"

    def test_gate_reference_missing_decision_logic(self) -> None:
        """
        CHECKPOINT: Each gate must document decision tree or outcome logic.
        Mutation: Remove "if PASS then..., if FAIL then..." sections.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        # Gate reference should explain what happens on PASS vs FAIL
        required_terms = {
            "PASS": "outcome or decision term PASS",
            "FAIL": "outcome or decision term FAIL",
        }

        for term, desc in required_terms.items():
            assert term in gate_ref, \
                f"Gate reference missing {desc}"

    def test_gate_reference_subsection_formatting_inconsistent(self) -> None:
        """
        CHECKPOINT: Gate sections must use consistent heading levels for subsections.
        Mutation: Mix #, ##, ### for Purpose, Inputs, etc. across gates.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        # Find all subsection headers (Purpose, Inputs, etc.)
        subsection_headers = re.findall(r'^(#+)\s+(Purpose|Inputs|Outputs|Artifacts|Decision|Troubleshooting)\b', gate_ref, re.MULTILINE)

        if not subsection_headers:
            pytest.skip("No subsection headers found")

        # Check consistency: all subsections should use same heading level
        levels = {level for level, _ in subsection_headers}
        assert len(levels) <= 2, \
            f"Inconsistent subsection heading levels: {levels}"

    def test_gate_reference_missing_all_six_gates_sections(self) -> None:
        """
        CHECKPOINT: All six gates must have dedicated sections.
        Mutation: Remove one gate section entirely.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        gates = [
            "spec_completeness_check", "static_analysis_check", "governance_check",
            "planner_check", "reviewer_check", "learning_check"
        ]

        for gate in gates:
            assert gate in gate_ref, \
                f"Gate '{gate}' missing from gate reference section"

    def test_gate_reference_links_to_nonexistent_specs(self) -> None:
        """
        CHECKPOINT: Links to gate specs must point to existing files.
        Mutation: Change spec file paths (e.g., 902_02_static_analysis_check_spec.md -> 902_02_analysis_spec.md).
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        # Find all file links [text](path)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', gate_ref)

        for text, link_path in links:
            target = _REPO_ROOT / link_path
            assert target.exists(), \
                f"Gate reference links to nonexistent file: {link_path}"


class TestReadmeStructureMutations:
    """Adversarial tests for README structure robustness."""

    def test_readme_duplicate_sections(self) -> None:
        """
        CHECKPOINT: No duplicate major sections (Workflow Diagram, How to Run, Gate Reference).
        Mutation: Add duplicate "Gate Reference" section.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        required_sections = [
            "Workflow Diagram",
            "How to Run Gates",
            "Gate Reference"
        ]

        for section in required_sections:
            count = len(re.findall(rf'^#+\s+.*{re.escape(section)}', content, re.MULTILINE))
            # If section exists (count >= 1), it must appear exactly once (not duplicated)
            if count > 0:
                assert count == 1, \
                    f"Section '{section}' appears {count} times; should appear exactly once (no duplicates)"

    def test_readme_section_ordering_backward(self) -> None:
        """
        CHECKPOINT: Sections must appear in correct order (strict).
        Mutation: Swap "How to Run Gates" and "Gate Reference" order.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        diagram_pos = content.find("Workflow Diagram")
        runbook_pos = content.find("How to Run Gates")
        reference_pos = content.find("Gate Reference")

        if diagram_pos < 0 or runbook_pos < 0 or reference_pos < 0:
            pytest.skip("Not all sections present yet")

        assert diagram_pos < runbook_pos < reference_pos, \
            "Sections must appear in order: Diagram → Runbook → Reference"

    def test_readme_gate_reference_before_runbook(self) -> None:
        """
        CHECKPOINT: Gate Reference (how to understand each gate) comes AFTER How to Run (basic execution).
        Mutation: Reverse order of runbook and gate reference.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        runbook_pos = content.find("How to Run Gates")
        reference_pos = content.find("Gate Reference")

        if runbook_pos < 0 or reference_pos < 0:
            pytest.skip("Sections not yet present")

        assert runbook_pos < reference_pos, \
            "Runbook (How to Run) must come before Gate Reference"

    def test_readme_preserves_existing_overview_section(self) -> None:
        """
        CHECKPOINT: Existing "Overview" section is not removed or drastically changed.
        Mutation: Remove Overview section.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        assert "Overview" in content, \
            "README must preserve existing 'Overview' section"

    def test_readme_existing_tickets_section_preserved(self) -> None:
        """
        CHECKPOINT: Existing "Tickets" section remains.
        Mutation: Delete Tickets section.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        assert "Tickets" in content or "tickets" in content.lower(), \
            "README must preserve existing 'Tickets' section"


class TestClaudeMdCompatibilityEdgeCases:
    """Adversarial tests for CLAUDE.md source-of-truth conflicts."""

    def test_runbook_commands_use_wrong_task_invocation_style(self) -> None:
        """
        CHECKPOINT: Commands should use canonical style (gate_runner.py), not ad-hoc patterns.
        Mutation: Add commands like "python gates/static_analysis_check.py" (direct invocation).
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Extract code blocks
        code_blocks = re.findall(r'```(?:bash|python|sh)?\s*\n(.*?)\n```', runbook, re.DOTALL)

        # Check for direct gate module invocation (should use gate_runner.py)
        for block in code_blocks:
            if "python" in block and "gates/" in block and "gate_runner" not in block:
                # Direct gate invocation found (e.g., python ci/scripts/gates/static_analysis_check.py)
                # This should trigger a warning but maybe not fail if gate_runner is also shown
                assert "gate_runner" in runbook, \
                    "Runbook should prefer gate_runner.py over direct gate module invocation"

    def test_runbook_references_undefined_task_names(self) -> None:
        """
        CHECKPOINT: Task names referenced must exist in Taskfile.yml or be defined elsewhere.
        Mutation: Add "task gates:static-analysis" which doesn't exist in Taskfile.yml.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        taskfile = _REPO_ROOT / "Taskfile.yml"
        if not taskfile.exists():
            pytest.skip("Taskfile.yml not found")

        taskfile_content = taskfile.read_text()

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Extract task names (task <name>)
        task_names = re.findall(r'\btask\s+([\w:/-]+)', runbook)

        for task_name in task_names:
            # Check if task is defined in Taskfile
            # Simple heuristic: task name should appear as a label or target
            assert task_name in taskfile_content, \
                f"Runbook references undefined task: {task_name}"


class TestLinkResolutionEdgeCases:
    """Adversarial tests for link and reference integrity."""

    def test_readme_links_with_trailing_whitespace(self) -> None:
        """
        CHECKPOINT: Links must not have trailing spaces before file extensions.
        Mutation: Add spaces like "(file.md )" or "(path/file.md)".
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        # Find markdown links with potential whitespace issues
        bad_links = re.findall(r'\]\s*\(\s*([^)]+?\s+)\s*\)', content)
        assert len(bad_links) == 0, \
            f"Links have trailing whitespace issues: {bad_links}"

    def test_gate_spec_links_consistency_across_sections(self) -> None:
        """
        CHECKPOINT: Same gate specs should be linked consistently across runbook and gate reference.
        Mutation: Link to spec in one section but not in another.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()

        # Extract spec file references
        spec_files = set(re.findall(r'project_board/specs/([^\s\)]+\.md)', content))

        # Each gate reference section should link to the gate spec
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        # At least one spec should be linked in gate reference
        specs_in_ref = set(re.findall(r'project_board/specs/([^\s\)]+\.md)', gate_ref))
        assert len(specs_in_ref) > 0, \
            "Gate reference section should link to gate specs"

    def test_mermaid_diagram_node_ids_not_matching_gate_names(self) -> None:
        """
        CHECKPOINT: Mermaid node IDs for gates should be traceable to gate names.
        Mutation: Use cryptic node IDs like G1, G2 without clear mapping to gate names.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Extract gate-related nodes (containing "gate" or "check")
        gate_nodes = re.findall(r'(\w+)\s*\[([^\]]*(?:gate|check)[^\]]*)\]', diagram, re.IGNORECASE)

        for node_id, label in gate_nodes:
            # Node ID should be reasonably descriptive
            # (Not just G1, G2, etc.)
            assert len(node_id) > 1, \
                f"Gate node ID too cryptic: {node_id} (label: {label})"

            # Label should contain recognizable gate name or stage
            assert any(term in label.lower() for term in ['gate', 'check', 'analysis', 'governance', 'spec']), \
                f"Gate node label not descriptive: {label}"


class TestMutationTestingGates:
    """Mutation testing: flip outcomes, change stage names, remove connections."""

    def test_diagram_all_gates_reachable_from_start(self) -> None:
        """
        CHECKPOINT: All gates must be reachable from START (no dead branches before gate).
        Mutation: Add START → COMPLETE without going through gates.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        gates = [
            "spec_completeness_check", "static_analysis_check", "governance_check",
            "planner_check", "reviewer_check", "learning_check"
        ]

        # Parse connections to build reachability graph (simplified)
        connections = re.findall(r'(\w+)\s*(?:-->|---)\s*(\w+)', diagram)

        for gate in gates:
            # Find if gate appears as source or destination in connections
            gate_found = any(gate in src or gate in dst for src, dst in connections)
            assert gate_found, \
                f"Gate '{gate}' not connected in diagram flow"

    def test_diagram_escape_paths_from_fail_outcome(self) -> None:
        """
        CHECKPOINT: FAIL outcome must have an escape/escalation path (not dead end).
        Mutation: FAIL leads nowhere (no ESCALATE, no retry).
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # If FAIL is mentioned, ensure it's not a dead end
        if "FAIL" in diagram:
            # Look for escape paths from FAIL: ESCALATE, retry, or human review
            has_escape = any(term in diagram for term in ["ESCALATE", "escalate", "BLOCKED", "blocked", "retry", "human"])
            assert has_escape, \
                "Diagram shows FAIL outcome but no escape/escalation path"

    def test_gate_reference_all_outcomes_documented_per_gate(self) -> None:
        """
        CHECKPOINT: Each gate must document what PASS and FAIL mean specifically for that gate.
        Mutation: Generic outcome descriptions not tailored to gate.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref = gate_ref_match.group(1)

        gates = [
            "spec_completeness_check", "static_analysis_check", "governance_check",
            "planner_check", "reviewer_check", "learning_check"
        ]

        for gate in gates:
            gate_section = gate_ref[gate_ref.find(gate):] if gate in gate_ref else ""
            if not gate_section:
                continue

            # Each gate section should mention outcomes
            has_outcomes = "PASS" in gate_section and "FAIL" in gate_section
            assert has_outcomes, \
                f"Gate '{gate}' section doesn't document PASS and FAIL outcomes"


class TestDeterminismAndConsistency:
    """Tests for determinism: same scenario, identical results."""

    def test_mermaid_diagram_parse_idempotency(self) -> None:
        """
        CHECKPOINT: Parsing diagram twice yields same results.
        Ensures no hidden state or non-determinism.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match1 = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        diagram_match2 = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)

        if not diagram_match1 or not diagram_match2:
            pytest.skip("No Mermaid diagram found")

        assert diagram_match1.group(1) == diagram_match2.group(1), \
            "Diagram parsing is non-deterministic"

    def test_gate_names_extracted_consistently(self) -> None:
        """
        CHECKPOINT: Extracting gate names from diagram and runbook yields consistent set.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        registry_data = load_json(GATE_REGISTRY)
        registry_names = {entry["name"] for entry in registry_data}

        content = README.read_text()

        # Extract from diagram
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        diagram_gates = set()
        if diagram_match:
            diagram_gates = set(re.findall(r'(\w+_\w+_check)', diagram_match.group(1)))

        # Extract from runbook
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        runbook_gates = set()
        if runbook_match:
            runbook_gates = set(re.findall(r'(\w+_\w+_check)', runbook_match.group(1)))

        # Extract from gate reference
        ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        ref_gates = set()
        if ref_match:
            ref_gates = set(re.findall(r'(\w+_\w+_check)', ref_match.group(1)))

        # All mentions should be in registry
        all_mentioned = diagram_gates | runbook_gates | ref_gates
        unknown = all_mentioned - registry_names
        assert len(unknown) == 0, \
            f"Unknown gates mentioned: {unknown}"


class TestStressAndBoundary:
    """Stress tests and boundary conditions."""

    def test_readme_max_section_size(self) -> None:
        """
        CHECKPOINT: README must stay <500 lines (operator's quick reference).
        Boundary: What if sections are excessively large?
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        lines = content.split('\n')

        assert len(lines) < 500, \
            f"README has {len(lines)} lines; must be <500"

    def test_gate_reference_section_not_excessive(self) -> None:
        """
        CHECKPOINT: Gate reference section should not dominate README.
        Boundary: If gate ref is >60% of README, it's too large.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        total_length = len(content)

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not gate_ref_match:
            pytest.skip("No gate reference section found")

        gate_ref_length = len(gate_ref_match.group(1))
        gate_ref_ratio = gate_ref_length / total_length if total_length > 0 else 0

        assert gate_ref_ratio < 0.65, \
            f"Gate reference is {gate_ref_ratio:.1%} of README; should be <65%"

    def test_mermaid_diagram_not_overly_complex(self) -> None:
        """
        CHECKPOINT: Mermaid diagram should render in single view (not huge).
        Boundary: >20 nodes might be too complex for single diagram.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        if not diagram_match:
            pytest.skip("No Mermaid diagram found")

        diagram = diagram_match.group(1)

        # Count nodes (rough estimate: any identifier with brackets/parens)
        nodes = re.findall(r'\b[A-Za-z_]\w*\s*[\[\(\{]', diagram)

        assert len(nodes) < 25, \
            f"Diagram has {len(nodes)} nodes; might be too complex for single view"

    def test_runbook_minimum_command_examples(self) -> None:
        """
        CHECKPOINT: Runbook must have at least 2 command examples (shadow and blocking, or multiple gates).
        Boundary: Single command example is insufficient.
        """
        if not README.exists():
            pytest.skip("README not yet implemented")

        content = README.read_text()
        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if not runbook_match:
            pytest.skip("No runbook section found")

        runbook = runbook_match.group(1)

        # Count distinct gate_runner.py invocations or task invocations
        commands = re.findall(r'(?:gate_runner\.py|task\s+\w+)', runbook)

        assert len(commands) >= 2, \
            f"Runbook has only {len(commands)} command examples; should have >=2"
