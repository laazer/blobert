"""Contract tests for M9 mesh/material audit ticket specification."""

from pathlib import Path

import pytest

_REPO_ROOT_DEPTH = 4
_REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
_TICKET_RELATIVE_PATHS = (
    "project_board/9_milestone_9_enemy_player_model_visual_polish/done/02_mesh_and_material_audit_enemy_families_and_player.md",
    "project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/02_mesh_and_material_audit_enemy_families_and_player.md",
    "project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/02_mesh_and_material_audit_enemy_families_and_player.md",
)


def _resolve_ticket_path() -> Path:
    for relative_path in _TICKET_RELATIVE_PATHS:
        candidate = _REPO_ROOT / relative_path
        if candidate.is_file():
            return candidate
    return _REPO_ROOT / _TICKET_RELATIVE_PATHS[0]

_REQUIREMENT_HEADINGS = (
    "### Requirement R1: Canonical Audit Scope (Enemy Families + Default Player)",
    "### Requirement R2: Deterministic Audit Rubric and Status Taxonomy",
    "### Requirement R3: Evidence Capture Schema and Spot-Check Protocol",
    "### Requirement R4: M13 Coordination Contract (Player Mutation Readability)",
    "### Requirement R5: Follow-on Tracking, Ownership, and Closure Gate",
)


def _ticket_text() -> str:
    ticket_path = _resolve_ticket_path()
    assert ticket_path.is_file(), f"Missing ticket at {ticket_path}"
    return ticket_path.read_text(encoding="utf-8")


def test_ticket_file_exists() -> None:
    assert _resolve_ticket_path().is_file()


@pytest.mark.parametrize("heading", _REQUIREMENT_HEADINGS)
def test_requirement_headings_present(heading: str) -> None:
    assert heading in _ticket_text()


def test_r1_requires_full_enemy_and_default_player_scope() -> None:
    text = _ticket_text()
    assert "No active enemy family is omitted; omissions are treated as spec failure" in text
    assert "multiple candidate player meshes" in text
    assert "default-play authoritative" in text
    assert "freeze marker (timestamp/revision)" in text


def test_r2_enforces_closed_status_set_and_fail_closed_pass_rule() -> None:
    text = _ticket_text()
    assert "exactly one final status in `{pass, fix-required, deferred}`" in text
    assert "`pass` is prohibited if any rubric dimension fails or is unverified" in text
    assert "`deferred` is prohibited unless a linked follow-on ticket identifier/name and owner are present" in text


def test_r2_rubric_dimensions_are_explicit() -> None:
    text = _ticket_text()
    for required in (
        "silhouette readability at gameplay distance",
        "clipping/interpenetration",
        "export integrity defects",
        "material identity/readability",
    ):
        assert required in text


def test_r3_requires_complete_row_evidence_schema() -> None:
    text = _ticket_text()
    assert "Required evidence fields per row" in text
    for required in (
        "asset identifier",
        "tool path used (`Godot` or `fallback`)",
        "capture notes for each rubric dimension",
        "status",
        "owner",
    ):
        assert required in text
    assert "Row without complete required fields is invalid and cannot be considered audited." in text


def test_r3_requires_spot_check_and_fallback_rationale() -> None:
    text = _ticket_text()
    assert "Spot-check notes are documented for at least one Godot validation pass per asset unless impossible" in text
    assert "impossibility requires explicit fallback rationale" in text
    assert "Asset cannot be loaded in either toolchain" in text
    assert "Mark `fix-required` with blocker details and open follow-on ticket" in text


def test_r4_m13_alignment_field_contract_is_explicit() -> None:
    text = _ticket_text()
    assert "M13 alignment field with one of: `aligned`, `conflict-opened`, `no-directive-found`." in text
    assert "`aligned` requires reference to specific M13 guidance artifact" in text
    assert "`conflict-opened` requires linked ticket and owner." in text


def test_r4_prevents_unqualified_pass_when_m13_is_missing_or_conflicting() -> None:
    text = _ticket_text()
    assert "unresolved conflicts cannot be marked `pass`." in text
    assert "`no-directive-found` cannot produce `pass` on contentious readability judgments" in text
    assert "Any contradiction between local recommendation and M13 is explicitly documented" in text


def test_r5_enforces_non_pass_linkage_and_owner_integrity() -> None:
    text = _ticket_text()
    assert "Every row with status `fix-required` or `deferred` has linked follow-on ticket ID/name and designated owner." in text
    assert "Zero non-pass rows remain with placeholder text (`TBD`, `None`, empty owner, or missing link)." in text
    assert "one-to-one mapping between non-pass findings and follow-on links." in text


def test_r5_requires_reconciled_closure_counts() -> None:
    text = _ticket_text()
    assert "includes counts by status and count of linked follow-on tickets; counts must reconcile." in text
    assert "cannot be considered complete until linkage reconciliation passes." in text


def test_workflow_state_lists_all_active_enemy_families_with_status() -> None:
    text = _ticket_text()
    assert "adhesion_bug" in text
    assert "acid_spitter" in text
    assert "claw_crawler" in text
    assert "carapace_husk" in text
    assert "status: `pass`" in text or "status: `fix-required`" in text or "status: `deferred`" in text


def test_workflow_state_includes_default_player_audit_evidence() -> None:
    text = _ticket_text()
    assert "player_3d" in text
    assert "default player" in text or "default-play" in text
    assert "M13 alignment" in text


def test_workflow_state_reconciles_non_pass_follow_on_links_and_owners() -> None:
    text = _ticket_text()
    assert "Non-pass reconciliation" in text
    assert "linked follow-on ticket" in text
    assert "owner" in text
    assert "Count reconciliation" in text


def test_workflow_state_documents_godot_and_fallback_spot_checks() -> None:
    text = _ticket_text()
    assert "Spot-check evidence" in text
    assert "Godot" in text
    assert "fallback" in text
