export const ENEMY_VERSIONS_SECTION_HEADING = "Enemy version slots & versions";

export const ENEMY_VERSIONS_HELP_PARAGRAPHS: readonly string[] = [
  "Slots are the runtime spawn pool per family (order is saved per family). Versions lists every registered row: Draft vs In pool and delete apply to the manifest immediately (separate from Save Slots).",
  "Draft versions are not slottable until you switch them to In pool. Use slots to order which in-pool variants spawn.",
  "Add slot first scans animated_exports/ for {family}_animated_*.glb files on disk and registers any missing variants in the manifest (then you pick which version to append to the slot list). Add empty slot appends an unassigned row (pick a version later, then Save slots).",
  "Use the Select column to choose multiple versions, then Set selected for draft / in pool or Delete selected (same rules as per-row delete).",
  "Name is an optional label in the manifest; edit the field and press Enter or click away to save.",
];

export const PLAYER_RESTART_REQUIREMENT_COPY =
  "Changes to player model selection are picked up on the next game load/restart. Live hot-reload is not guaranteed.";
export const LOAD_EXISTING_EMPTY_COPY = "No draft or in-use registry models available.";
export const ENEMY_EMPTY_SLOTS_COPY = "No slots assigned. Runtime falls back to legacy default path for this family.";
export const DRAFT_DELETE_CONFIRM_COPY =
  "Confirm irreversible draft delete. This removes the registry row and may also delete the draft file when file deletion is enabled.";
export const IN_USE_DELETE_CONFIRM_COPY =
  "Deleting an in-use version affects spawn eligibility and may be rejected by safety guards (for example: sole in-use version).";
