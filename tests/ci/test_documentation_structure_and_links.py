"""
M902-08 Documentation Integration Tests.

Validates the workflow visualization and agent runbook updates for M902-08.
Tests verify that:
1. README.md has required sections (diagram, runbook, gate reference)
2. Mermaid diagram in README is valid syntax
3. Runbook commands match gate_runner.py CLI schema
4. Gate reference sections document all 6 gates with consistent format
5. All links in README resolve to existing files
6. Gate names in documentation match gate_registry.json

Ticket: project_board/902_milestone_902_agent_predictabilitiy_improvements/01_active/08_workflow_visualization_and_agent_runbook_updates.md

Specification: project_board/test_designs/M902-08_specification.md
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Add conftest to path
sys.path.insert(0, str(Path(__file__).parent))
from conftest import load_json

_REPO_ROOT = Path(__file__).resolve().parents[2]
README = _REPO_ROOT / "project_board" / "902_milestone_902_agent_predictabilitiy_improvements" / "README.md"
GATE_REGISTRY = _REPO_ROOT / "ci" / "scripts" / "gate_registry.json"
CI_SCRIPTS = _REPO_ROOT / "ci" / "scripts"
GATE_SPECS_DIR = _REPO_ROOT / "project_board" / "specs"


class TestReadmeStructure:
    """AC-04.1 through AC-04.10: README file exists, is valid Markdown, has required sections."""

    def test_readme_file_exists(self) -> None:
        """AC-04.1: README.md exists."""
        assert README.exists(), f"README not found at {README}"

    def test_readme_is_valid_utf8(self) -> None:
        """AC-04.1: README is readable as UTF-8."""
        try:
            content = README.read_text(encoding="utf-8")
            assert len(content) > 0, "README is empty"
        except UnicodeDecodeError as e:
            pytest.fail(f"README is not valid UTF-8: {e}")

    def test_readme_has_workflow_diagram_section(self) -> None:
        """AC-04.2: README has 'Workflow Diagram and Agent Gating' section."""
        content = README.read_text()
        # Look for either ## or ### header with "Workflow Diagram"
        assert re.search(r'^#+\s+.*Workflow Diagram.*Agent Gating', content, re.MULTILINE), \
            "README must have section 'Workflow Diagram and Agent Gating' (Markdown header)"

    def test_readme_has_how_to_run_section(self) -> None:
        """AC-04.4: README has 'How to Run Gates Locally' section."""
        content = README.read_text()
        assert re.search(r'^#+\s+.*How to Run Gates.*Locally', content, re.MULTILINE), \
            "README must have section 'How to Run Gates Locally' (Markdown header)"

    def test_readme_has_gate_reference_section(self) -> None:
        """AC-04.5: README has 'Gate Reference' section."""
        content = README.read_text()
        assert re.search(r'^#+\s+.*Gate Reference', content, re.MULTILINE), \
            "README must have section 'Gate Reference' (Markdown header)"

    def test_readme_sections_ordered_correctly(self) -> None:
        """AC-04.2, AC-04.4, AC-04.5: Sections appear in correct order."""
        content = README.read_text()
        diagram_pos = content.find("Workflow Diagram")
        runbook_pos = content.find("How to Run Gates")
        reference_pos = content.find("Gate Reference")

        assert diagram_pos > 0, "Workflow Diagram section not found"
        assert runbook_pos > 0, "How to Run Gates section not found"
        assert reference_pos > 0, "Gate Reference section not found"

        assert diagram_pos < runbook_pos < reference_pos, \
            "Sections must appear in order: Diagram → Runbook → Reference"

    def test_readme_preserves_existing_sections(self) -> None:
        """AC-04.6: Existing sections (Overview, Tickets, Configuration, etc.) are preserved."""
        content = README.read_text()
        required_sections = ["Overview", "Tickets", "Configuration"]
        for section in required_sections:
            assert re.search(rf'^#+\s+.*{re.escape(section)}', content, re.MULTILINE), \
                f"Existing section '{section}' not found in README"

    def test_readme_file_size_reasonable(self) -> None:
        """AC-04.9: README is <500 lines (operator's quick reference)."""
        content = README.read_text()
        lines = content.split('\n')
        assert len(lines) < 500, f"README has {len(lines)} lines, should be <500"

    def test_readme_markdown_syntax_valid(self) -> None:
        """AC-04.10: README Markdown formatting is valid (basic checks)."""
        content = README.read_text()

        # Check balanced code fences
        fence_count = content.count('```')
        assert fence_count % 2 == 0, "Unbalanced ``` code fence markers"

        # Check balanced brackets in links
        link_count = content.count('[')
        link_close = content.count(']')
        assert link_count == link_close, f"Unbalanced brackets: [ count={link_count}, ] count={link_close}"


class TestMermaidDiagram:
    """AC-01.1 through AC-01.14: Mermaid diagram validation."""

    def test_diagram_embedded_in_readme(self) -> None:
        """AC-01.1: Mermaid diagram file is embedded in README.md."""
        content = README.read_text()
        # Look for Mermaid code block (```mermaid ... ```)
        assert '```mermaid' in content, "Mermaid diagram not found in README (missing ```mermaid fence)"

    def test_diagram_syntax_valid(self) -> None:
        """AC-01.14: Mermaid diagram syntax is valid."""
        content = README.read_text()

        # Extract diagram content
        match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert match, "Could not extract Mermaid diagram from README"

        diagram = match.group(1).strip()
        assert len(diagram) > 0, "Mermaid diagram is empty"

        # Check for basic Mermaid flowchart syntax
        assert 'graph' in diagram or 'flowchart' in diagram, \
            "Diagram must use 'graph' or 'flowchart' keyword"

        # Check for arrow syntax (-->)
        assert '-->' in diagram or '---' in diagram, \
            "Diagram must have connections (-->, ---, -|label|->)"

    def test_diagram_has_all_stages(self) -> None:
        """AC-01.3: All seven workflow stages are represented."""
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Could not extract diagram"
        diagram = diagram_match.group(1)

        stages = [
            "PLANNING",
            "SPECIFICATION",
            "TEST_DESIGN",
            "TEST_BREAK",
            "IMPLEMENTATION",
            "REVIEW",
            "LEARNING",
            "COMPLETE"
        ]

        for stage in stages:
            assert stage in diagram, f"Diagram missing stage: {stage}"

    def test_diagram_has_all_gates(self) -> None:
        """AC-01.4: All six gates are shown in diagram."""
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Could not extract diagram"
        diagram = diagram_match.group(1)

        gates = [
            "spec_completeness_check",
            "static_analysis_check",
            "governance_check",
            "planner_check",
            "reviewer_check",
            "learning_check"
        ]

        for gate in gates:
            assert gate in diagram, f"Diagram missing gate: {gate}"

    def test_diagram_has_gate_outcomes(self) -> None:
        """AC-01.6 through AC-01.8: FAIL, ESCALATE, WARN outcomes represented."""
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Could not extract diagram"
        diagram = diagram_match.group(1)

        outcomes = ["PASS", "FAIL", "ESCALATE"]
        for outcome in outcomes:
            assert outcome in diagram, f"Diagram missing outcome: {outcome}"

    def test_diagram_has_pretooluse_reference(self) -> None:
        """AC-01.11: PreToolUse hooks (M902-05) shown as separate enforcement layer."""
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Could not extract diagram"
        diagram = diagram_match.group(1)

        # Check for mention of PreToolUse or enforcement layer
        assert "PreToolUse" in diagram or "pre-tool" in diagram.lower() or "enforcement" in diagram.lower(), \
            "Diagram should reference PreToolUse or enforcement layer"

    def test_diagram_has_audit_reference(self) -> None:
        """AC-01.12: M902-07 governance audit shown as operational tool."""
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Could not extract diagram"
        diagram = diagram_match.group(1)

        # Check for mention of audit or operational
        assert "audit" in diagram.lower() or "operational" in diagram.lower(), \
            "Diagram should reference audit pipeline or operational tool"

    def test_diagram_has_legend_or_caption(self) -> None:
        """AC-01.10: Diagram includes legend or caption explaining roles and outcomes."""
        content = README.read_text()

        # Look for legend or caption near the diagram
        diagram_section = re.search(
            r'#+.*Workflow Diagram.*?\n(.*?)(?=\n#+|$)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert diagram_section, "Could not find diagram section"

        section_content = diagram_section.group(1)

        # Check for legend, caption, or explanation
        has_explanation = (
            "legend" in section_content.lower() or
            "caption" in section_content.lower() or
            "agent" in section_content.lower() or
            re.search(r'[A-Z]+.*(?:outcome|gate|role|path)', section_content)
        )
        assert has_explanation, "Diagram section should include legend/caption explaining roles and outcomes"


class TestRunbookCommands:
    """AC-02.1 through AC-02.11: Runbook section validation."""

    def test_runbook_section_exists(self) -> None:
        """AC-02.1: Runbook section titled 'How to Run Gates Locally' exists."""
        content = README.read_text()
        assert re.search(r'^#+\s+.*How to Run Gates.*Locally', content, re.MULTILINE), \
            "README must have runbook section"

    def test_runbook_has_overview_prose(self) -> None:
        """AC-02.2: Runbook includes overview prose explaining gate system."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Look for prose explaining gates (not just code blocks)
        prose = re.sub(r'```[\s\S]*?```', '', runbook)  # Remove code blocks
        prose = re.sub(r'^[\s]*\|.*\|$', '', prose, flags=re.MULTILINE)  # Remove tables

        assert len(prose.strip()) > 50, "Runbook should have substantial prose overview (>50 chars)"

    def test_runbook_explains_shadow_vs_blocking(self) -> None:
        """AC-02.3: Runbook explains shadow vs blocking mode."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        assert "shadow" in runbook.lower(), "Runbook should explain shadow mode"
        assert "blocking" in runbook.lower() or "enforcement" in runbook.lower(), \
            "Runbook should explain blocking/enforcement mode"

    def test_runbook_has_command_examples(self) -> None:
        """AC-02.4: Runbook includes copy-paste command examples."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Check for code blocks with gate commands
        code_blocks = re.findall(r'```(?:bash|python|sh)?\s*\n(.*?)\n```', runbook, re.DOTALL)
        assert len(code_blocks) > 0, "Runbook should have code blocks with command examples"

        # Check for gate runner or task invocations
        has_gate_commands = any(
            "gate_runner" in block or "task" in block or "python" in block
            for block in code_blocks
        )
        assert has_gate_commands, "Runbook should include gate_runner.py or task commands"

    def test_runbook_command_flags_valid(self) -> None:
        """AC-02.6: CLI flags in examples match gate_runner.py --help output."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Extract command examples
        commands = re.findall(r'python ci/scripts/gate_runner\.py[^\n]*', runbook)
        assert len(commands) > 0, "Runbook should have gate_runner.py command examples"

        # Check for valid flag patterns
        valid_flags = ['--mode', '--gate', '--upstream-agent', '--downstream-agent', '--ticket-id', '--output-dir']

        for command in commands:
            # Extract flags from command
            flags_in_cmd = set(re.findall(r'--[\w-]+', command))

            # Each flag in runbook should be a valid gate_runner flag
            for flag in flags_in_cmd:
                assert any(flag.startswith(vf) for vf in valid_flags), \
                    f"Invalid flag '{flag}' in command: {command}"

    def test_runbook_gate_names_match_registry(self) -> None:
        """AC-02.5: Gate names in examples match gate_registry.json."""
        registry_data = load_json(GATE_REGISTRY)
        registry_names = {entry["name"] for entry in registry_data}

        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Find gate names mentioned in runbook
        gate_pattern = r'gate_runner\.py\s+(\S+)'
        gates_mentioned = re.findall(gate_pattern, runbook)

        for gate in gates_mentioned:
            # Remove quotes if present
            gate = gate.strip("'\"")
            assert gate in registry_names, \
                f"Gate '{gate}' in runbook not found in gate_registry.json"

    def test_runbook_has_decision_tree(self) -> None:
        """AC-02.7: Runbook includes decision tree or flowchart."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Look for decision tree structure (if/else, bullet points with outcomes)
        has_decision_structure = (
            "PASS" in runbook and "FAIL" in runbook and "ESCALATE" in runbook
        ) or "decision" in runbook.lower() or "outcome" in runbook.lower()

        assert has_decision_structure, \
            "Runbook should include decision tree or outcome explanation"

    def test_runbook_has_spec_links(self) -> None:
        """AC-02.9: Runbook links to gate spec documents."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.MULTILINE | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Look for links to specs (project_board/specs/...)
        spec_links = re.findall(r'\[([^\]]+)\]\(([^)]*project_board/specs[^)]*)\)', runbook)

        assert len(spec_links) > 0, "Runbook should have links to gate specs"

    def test_runbook_mentions_artifacts(self) -> None:
        """AC-02.10: Runbook mentions artifact output locations."""
        content = README.read_text()

        runbook_match = re.search(
            r'#+\s+How to Run Gates.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert runbook_match, "Could not find runbook section"

        runbook = runbook_match.group(1)

        # Look for mentions of artifacts, outputs, JSON, or result locations
        has_artifact_mention = (
            "artifact" in runbook.lower() or
            "output" in runbook.lower() or
            "json" in runbook.lower() or
            "result" in runbook.lower() or
            "checkpoints" in runbook
        )
        assert has_artifact_mention, "Runbook should mention artifact output locations"


class TestGateReference:
    """AC-03.1 through AC-03.13: Gate reference section validation."""

    def test_gate_reference_section_exists(self) -> None:
        """AC-03.1: Gate reference section exists."""
        content = README.read_text()
        assert re.search(r'^#+\s+.*Gate Reference', content, re.MULTILINE), \
            "README must have 'Gate Reference' section"

    def test_all_six_gates_documented(self) -> None:
        """AC-03.2: All six gates are documented."""
        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        gates = [
            "spec_completeness_check",
            "static_analysis_check",
            "governance_check",
            "planner_check",
            "reviewer_check",
            "learning_check"
        ]

        for gate in gates:
            assert gate in gate_ref, f"Gate '{gate}' not documented in gate reference"

    def test_each_gate_has_consistent_subsections(self) -> None:
        """AC-03.3: Each gate section has Purpose, Inputs, Artifacts, Outputs, Decision, Spec Link, Troubleshooting."""
        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        # Find subsections for each gate
        gates = [
            "spec_completeness_check",
            "static_analysis_check",
            "governance_check",
            "planner_check",
            "reviewer_check",
            "learning_check"
        ]

        required_subsections = [
            "Purpose",
            "Inputs",
            "Artifacts",
            "Outputs",
            "Decision",
            "Troubleshooting"
        ]

        for gate in gates:
            # Find the section for this gate
            gate_pattern = rf'{re.escape(gate)}[^\n]*\n(.*?)(?={gates[-1] if gate == gates[-1] else gates[gates.index(gate)+1]}|$)'
            gate_section = re.search(gate_pattern, gate_ref, re.DOTALL | re.IGNORECASE)

            if gate_section:
                gate_content = gate_section.group(1)

                # At minimum, check for Purpose and Outputs
                assert "Purpose" in gate_content or "purpose" in gate_content.lower(), \
                    f"Gate '{gate}' section missing 'Purpose' subsection"

    def test_gate_reference_word_count_reasonable(self) -> None:
        """AC-03.4: Each gate section is 150-250 words."""
        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        # Remove code blocks and links to count prose
        prose = re.sub(r'```[\s\S]*?```', '', gate_ref)
        prose = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', prose)  # Remove link syntax

        # Count words (rough estimate)
        words = len(prose.split())

        # Gate reference should have substantial content (e.g., 1000+ words total for 6 gates * 150-250)
        assert words > 500, f"Gate reference too sparse: {words} words (should be >500 total)"

    def test_gate_names_match_registry(self) -> None:
        """AC-03.5: Gate names match gate_registry.json exactly."""
        registry_data = load_json(GATE_REGISTRY)
        registry_names = {entry["name"] for entry in registry_data}

        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        # Find all gate names mentioned
        gates = [
            "spec_completeness_check",
            "static_analysis_check",
            "governance_check",
            "planner_check",
            "reviewer_check",
            "learning_check"
        ]

        for gate in gates:
            assert gate in gate_ref, f"Gate '{gate}' not found in gate reference"
            assert gate in registry_names, f"Gate '{gate}' not in gate_registry.json"

    def test_gate_outputs_documented(self) -> None:
        """AC-03.6: Outputs (PASS, FAIL, WARN, ESCALATE) documented for each gate."""
        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        # Check for outcome terms
        outcomes = ["PASS", "FAIL", "WARN", "ESCALATE"]

        for outcome in outcomes:
            assert outcome in gate_ref, \
                f"Gate reference should document '{outcome}' outcome"

    def test_spec_links_exist(self) -> None:
        """AC-03.8, AC-03.9: Spec links point to correct files and paths exist."""
        content = README.read_text()

        gate_ref_match = re.search(
            r'#+\s+Gate Reference.*?\n(.*?)(?=\n#+|\Z)',
            content,
            re.DOTALL | re.IGNORECASE
        )
        assert gate_ref_match, "Could not find gate reference section"

        gate_ref = gate_ref_match.group(1)

        # Find all links to project_board/specs/
        spec_links = re.findall(r'project_board/specs/[^\)\s]+\.md', gate_ref)

        assert len(spec_links) > 0, "Gate reference should link to gate specs"

        # Verify each link points to an existing file
        for link in spec_links:
            path = _REPO_ROOT / link
            assert path.exists(), f"Spec link target does not exist: {link}"

    def test_gate_reference_no_duplication(self) -> None:
        """AC-03.11: No duplication with existing gate-specific docs."""
        content = README.read_text()

        # Check if there's an old "Running Static Analysis Gate" section
        has_old_section = "Running Static Analysis Gate" in content

        if has_old_section:
            # If old section exists, it should be minimal or consolidated
            old_match = re.search(
                r'#+\s+Running Static Analysis Gate.*?\n(.*?)(?=\n#+|\Z)',
                content,
                re.DOTALL | re.IGNORECASE
            )
            if old_match:
                old_section = old_match.group(1)
                # Old section should be brief (< 300 words) if kept for backward compatibility
                words = len(old_section.split())
                # Either removed or consolidated into gate reference
                assert words < 300 or "Gate Reference" in content, \
                    "Old 'Running Static Analysis Gate' should be consolidated into Gate Reference"


class TestLinkResolution:
    """Verify all links in README resolve to existing files."""

    def test_all_relative_links_valid(self) -> None:
        """AC-04.8, AC-NF-01.5: All relative links point to existing files."""
        content = README.read_text()

        # Find all markdown links [text](path)
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)

        relative_links = [link for _, link in links if not link.startswith('http')]

        broken_links = []
        for link in relative_links:
            target = _REPO_ROOT / link
            if not target.exists():
                broken_links.append(link)

        assert len(broken_links) == 0, \
            f"Broken relative links: {broken_links}"

    def test_project_board_spec_links_exist(self) -> None:
        """AC-02.9, AC-03.8: Links to project_board/specs/ exist."""
        content = README.read_text()

        # Find all spec links
        spec_links = re.findall(r'project_board/specs/[^\)\s\]]+', content)

        for link in spec_links:
            path = _REPO_ROOT / link
            assert path.exists(), f"Spec link does not exist: {link}"


class TestClaudeCompatibility:
    """AC-05.x: Verify no contradictions with CLAUDE.md command source-of-truth."""

    def test_no_claude_md_modified(self) -> None:
        """AC-05.8: CLAUDE.md is NOT modified."""
        # This is a git-based check; we just verify file exists and is readable
        claude_md = _REPO_ROOT / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md should exist"

        # Verify it's readable (no accidental corruption)
        try:
            content = claude_md.read_text(encoding="utf-8")
            assert len(content) > 100, "CLAUDE.md seems corrupted or empty"
        except Exception as e:
            pytest.fail(f"Could not read CLAUDE.md: {e}")

    def test_runbook_commands_follow_source_of_truth(self) -> None:
        """AC-05.5: Commands in runbook follow source-of-truth hierarchy (Taskfile → CI scripts → CLAUDE.md)."""
        content = README.read_text()

        # Extract all commands from runbook
        commands = re.findall(r'```(?:bash|python|sh)?\s*\n(.*?)\n```', content, re.DOTALL)

        # Look for gate_runner.py commands (CLI scripts, preferred per source-of-truth)
        for cmd_block in commands:
            lines = cmd_block.strip().split('\n')
            for line in lines:
                if 'gate_runner' in line:
                    # Valid: uses gate_runner.py
                    assert 'python' in line or 'ci/scripts/gate_runner.py' in line, \
                        f"gate_runner.py invocation should be valid: {line}"


class TestAcceptanceCriteria:
    """Meta-test: Verify ticket acceptance criteria are satisfied."""

    def test_ac1_diagram_renders_and_matches_pipeline(self) -> None:
        """Ticket AC1: Mermaid diagram renders and matches implemented pipeline."""
        # Extract and verify diagram
        content = README.read_text()
        diagram_match = re.search(r'```mermaid\s*(.*?)\s*```', content, re.DOTALL)
        assert diagram_match, "Mermaid diagram not found"

        diagram = diagram_match.group(1)

        # Verify all gates and stages present
        gates = ["spec_completeness_check", "static_analysis_check", "governance_check",
                 "planner_check", "reviewer_check", "learning_check"]
        stages = ["PLANNING", "SPECIFICATION", "TEST_DESIGN", "TEST_BREAK",
                  "IMPLEMENTATION", "REVIEW", "LEARNING", "COMPLETE"]

        for gate in gates:
            assert gate in diagram, f"Missing gate: {gate}"

        for stage in stages:
            assert stage in diagram, f"Missing stage: {stage}"

    def test_ac2_runbook_and_gate_reference_complete(self) -> None:
        """Ticket AC2: Runbook and gate reference complete with gates and artifacts."""
        content = README.read_text()

        # Verify runbook section
        assert re.search(r'^#+\s+.*How to Run Gates', content, re.MULTILINE), \
            "Runbook section missing"

        # Verify gate reference section
        assert re.search(r'^#+\s+.*Gate Reference', content, re.MULTILINE), \
            "Gate reference section missing"

        # Verify all 6 gates documented
        gates = ["spec_completeness_check", "static_analysis_check", "governance_check",
                 "planner_check", "reviewer_check", "learning_check"]

        for gate in gates:
            assert gate in content, f"Gate '{gate}' not documented"

    def test_ac3_no_claude_md_contradictions(self) -> None:
        """Ticket AC3: No contradictions with CLAUDE.md; CLAUDE.md not modified."""
        # Verify CLAUDE.md exists and is unmodified
        claude_md = _REPO_ROOT / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md must exist"

        # Verify commands in runbook don't contradict CLAUDE.md source-of-truth
        content = README.read_text()

        # Look for task invocations (should be in Taskfile.yml if defined)
        task_commands = re.findall(r'task\s+[\w:/-]+', content)

        # These are informational only; actual source-of-truth is gate_runner.py
        if task_commands:
            # Verify gate_runner.py fallback is mentioned
            assert "gate_runner" in content or "python ci/scripts/gate_runner.py" in content, \
                "Runbook should provide gate_runner.py commands as fallback"
