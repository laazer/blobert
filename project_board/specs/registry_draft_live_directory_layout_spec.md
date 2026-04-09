# Registry draft vs live on-disk layout

**Spec ID:** RDL-1  
**Ticket:** `13_registry_paths_align_with_draft_vs_in_use_directories.md`

## Layout (under `asset_generation/python/`)

| Asset class | Live (non-draft, canonical pool files) | Draft |
|-------------|----------------------------------------|--------|
| Animated enemies | `animated_exports/{stem}.glb` | `animated_exports/draft/{stem}.glb` |
| Player | `player_exports/{name}.glb` | `player_exports/draft/{name}.glb` |
| Level objects | `level_exports/{name}.glb` | `level_exports/draft/{name}.glb` |

- **`exports/`** (static) is unchanged; no `draft/` split in this spec.
- **Companion files** move with the GLB: `{stem}.attacks.json` (animated), `{stem}.player.json` (player), `{stem}.object.json` (level).

## Allowlist / URLs

- Registry paths remain under existing prefixes (`animated_exports/`, etc.); draft files use the extra `draft/` segment.
- `/api/assets/animated_exports/draft/foo.glb` is valid; traversal rules unchanged.

## Export

- When `BLOBERT_EXPORT_USE_DRAFT_SUBDIR=1` is set in the environment (editor run stream with `output_draft=true`), Blender exports for `animated`, `player`, and `level` write into the `draft/` subtree for that root.
- Default CLI (env unset): live root only (backward compatible).

## Promote / demote (registry patch)

- `patch_enemy_version` / `patch_player_version`: after applying `draft` / `in_use` patches and MRVC coercion, if the row’s path is a managed `{root}/*.glb` or `{root}/draft/*.glb`, the service **moves** the GLB (+ sidecars) to match the final `draft` flag and updates `path`.
- If the destination GLB already exists and is not the same file as the source → **ValueError** (refuse overwrite).
- If the source GLB is missing but the destination exists → update registry path only (recoverable).
- If both missing → update path only.

## Discovery (`sync_*`)

- `sync_discovered_animated_glb_versions` scans `animated_exports/*.glb` and `animated_exports/draft/*.glb`.
- `sync_discovered_player_glb_versions` scans `player_exports/*.glb` and `player_exports/draft/*.glb`.

## Migration from flat draft files

- Legacy rows may have `draft: true` and `path: animated_exports/foo.glb`. Validation still allows this.
- Operators can promote/demote once in the editor to move onto the new layout, or move files manually and edit `model_registry.json`.

## Git

- Optional: ignore `**/animated_exports/draft/**`, `**/player_exports/draft/**`, `**/level_exports/draft/**` locally; commit only live roots for shipped assets. Not enforced in-repo.
