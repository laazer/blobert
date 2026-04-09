# TICKET: 12_enemy_body_part_extras_editor_ui

Title: Asset editor — “Extras” tab and per-body-part extra + material UI

## Description

Add a third **material-adjacent** center-panel tab **Extras** alongside **Build** and **Colors** in the asset editor, using the same “setup” mental model as **Colors** (per animated enemy slug, driven by API-defined controls).

**UI behavior (v1):**

- New **Extras** tab in the center switch bar (same region as Code / Build / Colors / Registry today — see `asset_generation/web/frontend/src/components/layout/ThreePanelLayout.tsx`).
- For each body part / zone that supports extras (as reported by the backend control definitions from ticket **11**), show:
  - **Extra type** selector: none, shell, spikes, horns, bulbs (exact enum from spec **11**).
  - **Type-specific fields** where applicable: spike primitive (cone vs pyramid), spike count, bulb count, etc.
  - **Material + color** for the extra geometry on that part (finish + hex where the API exposes them), mirroring the **Colors** tab pattern (`FeatureMaterialControls` / `ColorsPane` family of components — reuse patterns, do not duplicate sanitization logic inconsistently).
- Enforce **one extra type per part** in the UI (disable conflicting selections or show validation inline consistent with backend errors).

**Store / wiring:** Extend `useAppStore` (or equivalent) so the Extras tab reads and writes the same build-options document the preview / export path consumes, consistent with how Build and Colors panels sync today.

## Acceptance Criteria

- **Extras** tab is visible and functional for at least one reference animated enemy slug end-to-end (select type → counts → material/color → preview refresh or rebuild matches ticket **11** behavior).
- Empty / unsupported slug shows a clear empty state (same quality bar as `ColorsPane` / `FeatureMaterialControls`).
- Frontend tests cover: tab presence, at least one control round-trip or store update for extras keys (follow existing `*.test.tsx` conventions under `asset_generation/web/frontend`).
- `npm test` and `npm run build` pass in `asset_generation/web/frontend`.
- Full repo validation: `timeout 300 ci/scripts/run_tests.sh` exits 0 once ticket **11** is merged or the UI is feature-flagged only in a way CI still passes (prefer implementing after **11**).

## Dependencies

- **Hard:** `backlog/11_enemy_body_part_extras_spec_and_pipeline.md` — API control definitions and option keys must exist before the UI can be finalized.

## Execution plan

1. After **11**: confirm control defs shape from `animated_build_controls_for_api()` (or successor).
2. Add `centerPanel === "extras"` (or agreed key), `ExtrasPane.tsx` (or grouped sections inside a shared shell), and tab button in `ThreePanelLayout.tsx`.
3. Implement reusable rows (extend `FeatureMaterialControls` or sibling component) for extra type + params + material/color per part.
4. Wire Zustand store + preview command path; add tests.

## Specification (summary)

- **Tab:** `centerPanel: "extras"` → `ExtrasPane` → `ZoneExtraControls`.
- **Defs:** `extra_zone_<zone>_*` from meta; `mergeCanonicalZoneControls` appends `syntheticExtraZoneDefsForSlug` when API omits rows (offline parity).
- **Build panel:** excludes `extra_zone_*` (with `feat_*`) so extras live only on Extras tab.
- **Kind UX:** `horns` option only on **head** zone; type-specific rows dimmed when inactive (`none` / `shell` / wrong kind).
- **Run path:** `animatedBuildOptionValues` already serializes non-mesh keys into `{ [slug]: { ... } }` for `BLOBERT_BUILD_OPTIONS_JSON` — no CommandPanel change required.

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
6

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passing — `npm test` / `npm run build` (frontend); `uv run pytest` including extended `test_slug_zone_extras_attach.py`; `timeout 300 ci/scripts/run_tests.sh` exit 0; diff-cover ≥ 85%.
- Static QA: Passing — TypeScript build clean.
- Integration: N/A (editor UI); run script covers Godot + Python + frontend unit scope per CI.

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{}
```

## Status
Proceed

## Reason

Extras tab, synthetic `extra_zone_*` merge, `ZoneExtraControls`, layout + store wiring, Build panel filter, tests; full CI green.
