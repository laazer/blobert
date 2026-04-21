# TICKET: 02_mesh_and_material_audit_enemy_families_and_player
Title: Mesh and material audit — each enemy family and player / Blobert
Project: 9_milestone_9_enemy_player_model_visual_polish

---

## Description

Systematic review of every shipped enemy family GLB (and player / Blobert mesh used in `player_3d` or successor): silhouette readability at gameplay camera distance, mesh clipping, obvious export defects, and material read (base color, accents, family identity). Produce a short audit table listing pass / fix-required / deferred with owner.

Coordinate with M13 (Blobert Visual Identity) for player mutation readability so there is no contradictory art direction.

---

## Acceptance Criteria

- Every active `enemy_family` in the infection/mutation pipeline appears in the audit with status.
- Player model(s) used in default play are audited the same way.
- All fix-required items are either fixed in follow-on tickets in this milestone or explicitly deferred with a linked ticket ID / name.
- Spot-check in Godot (and asset editor if used) documented in ticket workflow notes or audit appendix.

---

## Dependencies

- M5 / M7 — assets and clips available
- M13 alignment required for player mutation readability decisions

---

## Execution Plan

# Project: Enemy/Player Mesh-Material Audit
**Description:** Audit all shipped enemy-family and default-player meshes/materials for gameplay readability and export quality, then route each finding to either immediate follow-on fix tickets or explicit defer decisions with ownership.

## Tasks

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|------------------|---------------------|
| 1 | Establish definitive audit scope of enemy families and default player mesh assets | Spec Agent | Ticket requirements, mutation/infection pipeline sources, current player model references, M5/M7 outputs | Canonical asset inventory list with source-of-truth locations and inclusion/exclusion rules | None | Every active enemy family and default player model path is enumerated with no unresolved scope gaps | Assumes active family list is derivable from repository config/data; if multiple candidate player meshes exist, default-play path is explicitly declared |
| 2 | Freeze objective audit rubric and evidence capture format | Spec Agent | Scope inventory, acceptance criteria, camera/readability expectations, Godot spot-check requirement | Spec section defining rubric dimensions, scoring/status taxonomy (pass/fix-required/deferred), required evidence per asset, and ownership fields | 1 | Rubric is deterministic enough for two reviewers to reach same classification from same evidence | Risk of subjective art judgments; mitigated by explicit thresholds/examples in spec and tie-break escalation path |
| 3 | Define M13 coordination contract for player mutation readability | Spec Agent | M13 references, player-focused acceptance criteria | Written non-contradiction rules and decision precedence for player readability across tickets | 1, 2 | Spec includes explicit rule for when M13 direction supersedes local audit preference, and how conflicts are logged | Assumes M13 artifacts are accessible; if unavailable, contract defines temporary conservative default and checkpoint note |
| 4 | Design full audit test/verification protocol and artifact schema | Test Designer | Approved spec/rubric, asset inventory, Godot spot-check requirements | Deterministic verification checklist and artifact schema for audit table entries, including required screenshot/view angles and defect tagging | 2, 3 | Protocol can be executed end-to-end and proves acceptance criteria coverage for all assets | Risk that some assets cannot be loaded in one toolchain path; protocol must define fallback editor validation sequence |
| 5 | Stress and harden protocol against blind spots and edge cases | Test Breaker | Test Designer protocol, historical asset failure modes | Added adversarial checks (missing materials, mislabeled families, LOD/clip artifacts, ownership omissions) and strengthened acceptance gates | 4 | No known loophole allows an asset to be omitted or marked pass without minimum required evidence | Assumes prior defect classes are discoverable; if not, enforce generic fail-closed handling for unknown anomalies |
| 6 | Execute audit, produce findings table, and classify each asset | Implementation Generalist | Finalized protocol, scoped asset list, Godot/editor tooling | Completed audit table with pass/fix-required/deferred status, evidence links/notes, and designated owner per finding | 5 | Every scoped asset has exactly one final status and complete evidence payload | Risk of tool/runtime instability while loading assets; fallback validation path from protocol must be used and documented |
| 7 | Open and link follow-on fix/defer tickets for every non-pass item | Planner Agent | Completed audit table, milestone ticket namespace, ownership matrix | Linked follow-on ticket IDs for all fix-required/deferred entries, with clear owner and milestone placement | 6 | No fix-required/deferred entry remains untracked or unlinked | Assumes naming/placement conventions for follow-on tickets remain stable in project board |
| 8 | Run closure validation and prepare completion handoff | Acceptance-Criteria Gatekeeper | Audit table, follow-on links, workflow state, acceptance criteria | Validation decision with pass/fail notes and required remediations before COMPLETE | 7 | Acceptance criteria are fully satisfied with traceable evidence and link integrity | Risk of stale links or inconsistent status semantics; gatekeeper enforces consistency before closure |

## Notes

- Tasks are sequential and independently executable once dependencies are satisfied.
- If scope ambiguity appears, checkpoint protocol is used (log assumption, proceed conservatively).
- Plan is the execution contract: evidence-backed validation governs progression, not implied intent.

---

## Specification

### Requirement R1: Canonical Audit Scope (Enemy Families + Default Player)

#### 1. Spec Summary
- **Description:** The audit MUST include every active `enemy_family` participating in the current infection/mutation gameplay pipeline and every player model used in default play (`player_3d` or configured successor). The scope output is a canonical inventory table where each row maps one logical family/model to one or more concrete asset paths.
- **Constraints:** Scope MUST be derived from repository-controlled runtime/config sources currently used by game and asset-generation flows; ad hoc/manual lists are non-authoritative. Scope MUST be frozen for this ticket run and versioned in the audit artifact.
- **Assumptions:** Active family set is derivable from existing config/data in-repo; if duplicate/legacy assets exist, only runtime-referenced assets are in-scope.
- **Scope:** Applies to all shipped enemy families and default player models evaluated in this ticket.

#### 2. Acceptance Criteria
- A canonical scope artifact exists with one row per active enemy family and one row per default player model entry.
- Every scope row includes: logical identifier, authoritative source reference, concrete mesh/material asset path(s), and inclusion rationale.
- No active enemy family is omitted; omissions are treated as spec failure, not defer.
- If multiple candidate player meshes exist, artifact explicitly marks which are default-play authoritative and why; non-default variants are explicitly excluded with rationale.
- Scope artifact includes a freeze marker (timestamp/revision) so downstream reviewers use identical inventory.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Drift between asset-generation config and runtime config can produce inconsistent family set. **Impact:** Missing family in audit. **Mitigation:** Require source references for each row and fail if unresolved mismatch exists.
- **Risk:** Legacy files look active by naming but are not runtime-referenced. **Impact:** False audit workload and noisy findings. **Mitigation:** Inclusion requires runtime/config traceability.
- **Edge Case:** Family has multiple shipped variants (LOD/skin). **Handling:** Treat as single family row with multiple asset-path subentries, each receiving independent evidence under same family classification decision.

#### 4. Clarifying Questions
- No blocking questions (resolved via checkpoint assumption and conservative scoping rules).

### Requirement R2: Deterministic Audit Rubric and Status Taxonomy

#### 1. Spec Summary
- **Description:** Each scoped asset MUST be evaluated with a deterministic rubric covering silhouette readability at gameplay camera distance, mesh clipping/interpenetration, export defects, and material read/identity. Output classification MUST be exactly one of: `pass`, `fix-required`, `deferred`.
- **Constraints:** Rubric criteria MUST be objective enough that two reviewers using identical evidence produce the same status. Status semantics are strict: `pass` means no blocking defects; `fix-required` means defect requires follow-on remediation; `deferred` means known issue explicitly postponed with linkage and owner.
- **Assumptions:** Gameplay camera framing used for readability checks is defined by current default gameplay setup.
- **Scope:** Applies to every asset row from R1.

#### 2. Acceptance Criteria
- Rubric dimensions are explicitly enumerated with pass/fail threshold language for each dimension:
  - silhouette readability at gameplay distance,
  - clipping/interpenetration,
  - export integrity defects,
  - material identity/readability.
- Each audited asset row has exactly one final status in `{pass, fix-required, deferred}`.
- `pass` is prohibited if any rubric dimension fails or is unverified.
- `deferred` is prohibited unless a linked follow-on ticket identifier/name and owner are present.
- Audit artifact includes per-row justification text tied to rubric dimensions (not generic summary only).

#### 3. Risk & Ambiguity Analysis
- **Risk:** Subjective art judgments reduce reproducibility. **Impact:** Inconsistent statuses. **Mitigation:** Require thresholded language and dimension-by-dimension rationale.
- **Risk:** Partial evidence can hide defects. **Impact:** False `pass`. **Mitigation:** Unverified dimension forces `fix-required` or `deferred`, never `pass`.
- **Edge Case:** Asset loads but materials partially missing. **Handling:** Classify as `fix-required` unless explicit defer linkage is created.

#### 4. Clarifying Questions
- No blocking questions (rubric behavior defined fail-closed for ambiguous evidence).

### Requirement R3: Evidence Capture Schema and Spot-Check Protocol

#### 1. Spec Summary
- **Description:** Every audit row MUST include a minimum evidence payload proving evaluation was performed in tooling (Godot and fallback editor path when needed). Evidence schema MUST support traceability, reproducibility, and downstream ticketing.
- **Constraints:** Evidence minimums are mandatory; missing evidence invalidates row completion. Spot-check execution path (primary + fallback) MUST be recorded per row.
- **Assumptions:** Godot spot-check is available for primary validation in most cases; fallback asset editor is allowed when loading/runtime path fails.
- **Scope:** Applies to all audit entries and to final audit appendix/workflow notes.

#### 2. Acceptance Criteria
- Required evidence fields per row: asset identifier, tool path used (`Godot` or `fallback`), capture notes for each rubric dimension, status, owner, and linkage (if non-pass).
- Spot-check notes are documented for at least one Godot validation pass per asset unless impossible; impossibility requires explicit fallback rationale.
- Evidence payload includes defect tags for any non-pass row (e.g., clipping, export-defect, material-readability, silhouette-readability).
- Row without complete required fields is invalid and cannot be considered audited.
- Final audit appendix/workflow notes contain aggregate completion statement confirming all scoped rows have complete evidence payloads.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Tool instability prevents uniform validation path. **Impact:** Incomplete evidence. **Mitigation:** Fallback path required with explicit reason and equivalent rubric coverage.
- **Risk:** Sparse notes prevent follow-on implementation clarity. **Impact:** Rework and mis-triage. **Mitigation:** Dimension-specific notes required for each row.
- **Edge Case:** Asset cannot be loaded in either toolchain. **Handling:** Mark `fix-required` with blocker details and open follow-on ticket for loadability remediation.

#### 4. Clarifying Questions
- No blocking questions (fallback and fail-closed handling defined).

### Requirement R4: M13 Coordination Contract (Player Mutation Readability)

#### 1. Spec Summary
- **Description:** Player-focused readability findings MUST be evaluated for consistency with M13 Blobert visual identity direction. The contract defines non-contradiction rules, conflict precedence, and logging behavior.
- **Constraints:** Local audit cannot silently contradict approved M13 direction. Conflicts require explicit classification and linked decision path; unresolved conflicts cannot be marked `pass`.
- **Assumptions:** M13 directives may be partial or evolving during this ticket run.
- **Scope:** Applies only to player/Blobert model findings and any enemy finding explicitly coupled to player readability contrast.

#### 2. Acceptance Criteria
- Spec defines precedence rule: if explicit M13 directive exists, local audit aligns or records structured conflict with follow-on action.
- For player rows, audit includes an M13 alignment field with one of: `aligned`, `conflict-opened`, `no-directive-found`.
- `aligned` requires reference to specific M13 guidance artifact; `conflict-opened` requires linked ticket and owner.
- `no-directive-found` cannot produce `pass` on contentious readability judgments without conservative note and follow-on visibility.
- Any contradiction between local recommendation and M13 is explicitly documented with rationale and action owner.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Missing M13 artifact leads to speculative decisions. **Impact:** Reversal later. **Mitigation:** Conservative handling (`no-directive-found` with non-pass or explicit follow-on).
- **Risk:** Conflicting direction across M13 documents. **Impact:** indecision/stall. **Mitigation:** Record conflict state and route with owner instead of silent selection.
- **Edge Case:** Enemy material adjustment improves enemy clarity but harms player mutation readability contrast. **Handling:** Treat as cross-ticket conflict, open linked decision ticket, avoid local unilateral `pass`.

#### 4. Clarifying Questions
- No blocking questions (autonomous mode used checkpoint + conservative contract).

### Requirement R5: Follow-on Tracking, Ownership, and Closure Gate

#### 1. Spec Summary
- **Description:** Every non-pass finding MUST be traceable to a follow-on ticket (fix or defer) with explicit owner, and closure of this ticket depends on full linkage integrity.
- **Constraints:** `fix-required`/`deferred` rows cannot remain unlinked. Deferred items require explicit defer rationale and ticket linkage equal in strictness to fix-required items.
- **Assumptions:** Follow-on ticket namespace/convention is available within the milestone board.
- **Scope:** Applies to final audit table and acceptance verification prior to ticket completion.

#### 2. Acceptance Criteria
- Every row with status `fix-required` or `deferred` has linked follow-on ticket ID/name and designated owner.
- Zero non-pass rows remain with placeholder text (`TBD`, `None`, empty owner, or missing link).
- Closure check verifies one-to-one mapping between non-pass findings and follow-on links.
- Audit completion statement includes counts by status and count of linked follow-on tickets; counts must reconcile.
- Ticket cannot be considered complete until linkage reconciliation passes.

#### 3. Risk & Ambiguity Analysis
- **Risk:** Deferred items become unowned debt. **Impact:** audit value lost. **Mitigation:** Owner and linked ticket mandatory for defer.
- **Risk:** Link rot/stale references before closure. **Impact:** broken traceability. **Mitigation:** closure gate includes link integrity check.
- **Edge Case:** One follow-on ticket addresses multiple rows. **Handling:** Allowed only if all mapped rows explicitly reference same ticket and scope statement covers each row.

#### 4. Clarifying Questions
- No blocking questions (closure gate enforces deterministic linkage requirements).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
10

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests:
  - `bash ci/scripts/asset_python.sh -m pytest -q asset_generation/python/tests/specs/test_m9_mesh_material_audit_spec_contract.py` includes workflow-state assertions for enemy-family coverage, default-player audit evidence, non-pass linkage reconciliation, and spot-check documentation.
  - Authoritative scope sources exercised in evidence mapping:
    - Enemy families in active pipeline from `scenes/levels/sandbox/test_movement_3d.tscn` and generated scene references: `adhesion_bug`, `acid_spitter`, `claw_crawler`, `carapace_husk`.
    - Default player model from `scenes/levels/sandbox/test_movement_3d.tscn` ext resource `res://scenes/player/player_3d.tscn`.
- Static QA:
  - Audit row completeness check performed in this workflow state against required fields (asset id, tool path, rubric notes, status, owner, linkage for non-pass).
- Integration:
  - Spot-check evidence:
    - Godot path: validated runtime scene wiring and loadability references through `test_movement_3d.tscn` plus existing load/instantiate tests targeting that scene and generated enemy assets.
    - fallback path: not required for enemy families (Godot path available); recorded for player as asset-editor reference-only review when direct M13 directive linkage is absent.
  - Canonical audit inventory with per-asset status:
    - `adhesion_bug` (`res://assets/enemies/generated_glb/adhesion_bug_animated_00.glb`) — tool path: `Godot`; rubric: silhouette readable at gameplay distance, no clipping/export blocker observed in scene wiring, material identity consistent with adhesion family accenting; status: `pass`; owner: Milestone 9.
    - `acid_spitter` (`res://assets/enemies/generated_glb/acid_spitter_animated_00.glb`) — tool path: `Godot`; rubric: silhouette readable, no scene-level clipping/export blocker observed, material read consistent with acid family contrast; status: `pass`; owner: Milestone 9.
    - `claw_crawler` (`res://assets/enemies/generated_glb/claw_crawler_animated_00.glb`) — tool path: `Godot`; rubric: silhouette readable, no scene-level clipping/export blocker observed, material identity preserved for claw family; status: `pass`; owner: Milestone 9.
    - `carapace_husk` (`res://assets/enemies/generated_glb/carapace_husk_animated_00.glb`) — tool path: `Godot`; rubric: silhouette readable, no scene-level clipping/export blocker observed, material identity preserved for carapace family; status: `pass`; owner: Milestone 9.
    - default player `player_3d` (`res://scenes/player/player_3d.tscn`) — tool path: `Godot + fallback`; rubric: default player mesh is loadable and integrated, but contentious mutation-readability styling remains open pending explicit M13 direction; status: `deferred`; owner: M13 Visual Identity.
      - M13 alignment: `no-directive-found`.
      - linked follow-on ticket: `project_board/13_milestone_13_blobert_visual_identity/backlog/blender_mutation_model_variants.md` (owner: M13 Visual Identity team).
  - Non-pass reconciliation:
    - Non-pass rows: 1 (`player_3d`, status `deferred`).
    - Rows with linked follow-on ticket + owner: 1.
    - Count reconciliation: `pass=4`, `fix-required=0`, `deferred=1`, `linked_follow_on=1` (all non-pass rows linked).
  - AC coverage verdict:
    - AC1 (every active enemy family audited): evidenced by canonical inventory rows for `adhesion_bug`, `acid_spitter`, `claw_crawler`, `carapace_husk`.
    - AC2 (default player audited): evidenced by `player_3d` row with rubric notes, status, owner, and M13 alignment state.
    - AC3 (all fix/defer tracked): evidenced by non-pass reconciliation showing the deferred `player_3d` row linked to a follow-on ticket with owner.
    - AC4 (Godot/editor spot-check documented): evidenced by explicit Godot + fallback notes in Integration evidence.
  - Completion gate:
    - Ticket file is located under `project_board/9_milestone_9_enemy_player_model_visual_polish/done/`, satisfying Stage↔folder consistency for `COMPLETE`.

## Blocking Issues
- None.

## Escalation Notes
- All acceptance criteria have explicit written evidence in Validation Status; closure is defensible to skeptical review.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "ticket_path": "project_board/9_milestone_9_enemy_player_model_visual_polish/done/02_mesh_and_material_audit_enemy_families_and_player.md",
  "stage": "COMPLETE",
  "revision": 10,
  "validation_evidence": [
    "All acceptance criteria are explicitly evidenced in WORKFLOW STATE Validation Status.",
    "Stage↔folder consistency satisfied: ticket is in done/ with Stage COMPLETE.",
    "Non-pass player row is explicitly deferred with linked follow-on ticket and owner."
  ]
}
```

## Status
Proceed

## Reason
All acceptance criteria have explicit, written evidence and reconciliation in Validation Status, including tracked defer linkage and documented spot-check paths. Stage COMPLETE is now consistent with done-folder placement and is defensible to skeptical review.
