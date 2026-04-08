# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**blobert** is a Godot 4+ game project. The primary scripting language is GDScript.

## Reference projects (`reference_projects/`)

Third-party and demo Godot projects live under `reference_projects/`. Subdirectories may be used for implementation reference (patterns, APIs, scene structure, `project.godot` examples) **except** under Godot’s official demo repo: **ignore `reference_projects/godot-demo-projects/2d/`** — those are pure 2D demos and do not match blobert’s 3D scene target; prefer `3d/`, `xr/`, `viewport/`, and other non-`2d/` trees inside `godot-demo-projects/` when relevant. Treat the tree as read-only upstream material: do not add blobert game code or assets under `reference_projects/`, and do not point blobert’s `project.godot` at resources inside it. Examples include `reference_projects/3D-Platformer-Kit/` and `reference_projects/godot-demo-projects/` (excluding `2d/` as above).

## Development target: 3D scenes

Development is for **3D scenes**: 2.5D with one 3D world and 2D-like gameplay.

- **Main scene:** `res://scenes/levels/sandbox/test_movement_3d.tscn` (set in `project.godot` as `run/main_scene`).
- **Player:** `PlayerController3D` in `scripts/player/player_controller_3d.gd`; scene `scenes/player/player_3d.tscn`. Use **CharacterBody3D**, **Camera3D**, **Area3D**, **Node3D**, etc. for new gameplay and levels.
- **Movement logic:** Shared pure simulation in `scripts/movement/movement_simulation.gd` (no Node/Input); the 3D controller maps Vector2 → Vector3 and drives physics.
- **New tests** should use the 3D scene (see `tests/scenes/levels/test_3d_scene.gd`).

## Agent checkpoints (autopilot / autonomous agents)

- **Full checkpoint text** (`Would have asked` / `Assumption made` / `Confidence`) belongs only in scoped files: `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- **`project_board/CHECKPOINTS.md` is index-only:** run headers, resume pointers, one-line outcomes, and `Log:` paths. Do **not** append full checkpoint bodies or `**Would have asked:**` blocks there.

## Common Commands

`direnv` (see `.envrc`) puts `bin/godot` (headless wrapper) and `ci/scripts/` on PATH, sets `UV_PROJECT` to `asset_generation/python` so `uv run …` works from the repo root, and prepends that project’s `.venv/bin` to PATH when the venv exists (run `cd asset_generation/python && uv sync --extra dev` once).

**Hook / Task Python:** `ci/scripts/asset_python.sh` is the supported interpreter for Lefthook’s Python and GD reviewer steps (via `task hooks:py-parse`, `hooks:py-organization`, `hooks:gd-*`). It uses **only** `asset_generation/python/.venv/bin/python` or `uv run --extra dev python` from that project — not arbitrary `python3` on PATH. Pre-push pytest uses the same policy (`.lefthook/scripts/py-tests.sh`).

```bash
# Canonical full suite: Godot (bounded fail-fast import + tests) then asset_generation/python pytest
timeout 300 ci/scripts/run_tests.sh

# Godot-only (same 300s test timeout; import is not bundled here)
timeout 300 godot -s tests/run_tests.gd

# Force reimport (rebuilds class cache — run if tests fail to load scripts). Prefer bounded import via run_tests.sh in CI.
timeout 120 godot --headless --import

# asset_generation Python tests + coverage XML + diff-cover (same gate as pre-push; threshold from DIFF_COVER_FAIL_UNDER, default 85)
export DIFF_COVER_FAIL_UNDER="${DIFF_COVER_FAIL_UNDER:-85}"
cd asset_generation/python && uv run --extra dev pytest tests/ -q --cov=src --cov-config=pyproject.toml --cov-report=term-missing:skip-covered --cov-report=xml && uv run --extra dev python -m diff_cover.diff_cover_tool coverage.xml --compare-branch="${DIFF_COVER_COMPARE_BRANCH:-origin/main}" --fail-under="$DIFF_COVER_FAIL_UNDER"
```

## ⏱ Always Use Timeout

When invoking Godot outside of `ci/scripts/run_tests.sh`, use a timeout to prevent hanging:
- `timeout 300 godot -s tests/run_tests.gd` — Godot suite only
- `timeout 120 godot --headless --import` — import/reimport only (fail-fast; stderr not discarded)

## ⚠️ Do Not Use `--check-only`

`godot --check-only` hangs indefinitely in this project. In Godot 4.6.1 headless mode it initializes the main scene, which runs physics scripts without collision resolution — the enemy falls forever and the process never exits. The test runner catches parse errors directly (script load fails with an explicit error), so `--check-only` provides no additional safety.

## File Editing & Moves

Prefer `git mv` for renames/moves so history is preserved.

## Colocate configuration with what it configures

- **Keep tuning, defaults, and feature-specific constants next to the code they belong to** — typically as attributes on the class or private module-level names in the **same file** as that type. Do not introduce a sibling module whose only job is to hold values for a single class under another name (e.g. `*_params.py`, `*_settings.py`, `*_tuning.py`, `mesh_*`, `enemy_*_config`) unless those values are **shared by multiple types** or are a deliberate public API surface.
- **Shared cross-cutting constants** (used by many call sites or defining a reusable primitive) belong in a clearly scoped place: e.g. `asset_generation/python/src/core/rig_models/` for rig layouts and mesh helpers shared across enemy families (`QuadrupedRigLayout`, `MESH_BODY_CENTER_Z_FACTOR`). Prefer extending an existing shared module over adding a new grab-bag file.
- **Example (`asset_generation/python`):** procedural enemy mesh numbers live on each enemy model class (`AnimatedSpider`, …) as `ClassVar` fields; at build time `BaseAnimatedModel._mesh("NAME")` applies optional overrides from `build_options["mesh"]` (populated by the asset editor preview / CLI JSON). The editor exposes those knobs as float controls from introspection — no duplicate tuning list in a sidecar module.

## Code review agents (orchestrated subagents)

Orchestrators (`/feature`, `/autopilot`, `/bugfix`, `/ap-continue`, `/c-continue`, and any hand-off to `gdscript-reviewer` or **Python Reviewer Agent**) must instruct reviewers to read the relevant subsection below and enforce it on **new or changed lines** in the diff. Review order stays **organization first**, then **best practices** (as in each skill’s Stage 5b / 3b block).

### GDScript (`gdscript-reviewer`)

Treat **unexplained numeric literals** in gameplay, physics, timing, or presentation logic as findings unless clearly exempt:

- **Exempt:** `0`, `1`, `-1` (and similar) as neutral/identity, trivial loop bounds, or obvious array/slot indices; values already named via `const`, `enum`, or `@export`; standard built-ins (`Vector3.ZERO`, `Vector3.ONE`, `PI`, etc.); comparisons to zero where zero is the natural floor/reset (e.g. clearing a timer).
- **Not exempt:** “Tuning” floats/ints embedded in expressions (thresholds, durations, scales, damage, speeds) — use **class-scoped `const`** or `@export` on the same type, consistent with *Colocate configuration* above.
- **Severity:** New magic numbers in the change set are at least **non-blocking warnings**; repeated or high-impact literals (combat, HP, movement) should be **blocking** until named.

### Python (Python Reviewer Agent)

- **Lazy / deferred imports:** Prefer **normal module-level imports**. Do **not** move imports into functions or methods unless required to break a **documented import cycle** (or another hard constraint such as optional heavy dependencies used only behind a feature flag). If a lazy import is necessary, it must include a **short comment** naming the cycle or constraint. Flag new lazy imports without justification as **at least MEDIUM**; prefer fixing dependency direction or splitting modules over adding deferred imports.
- **Magic numbers:** Same spirit as GDScript — unexplained numeric literals for tuning, limits, timeouts, and domain thresholds should be **named** (`CONSTANT`, settings object, or dataclass field) at module or class scope near the code they configure, consistent with *Colocate configuration* above.

### Pre-commit automation (enforced locally)

These run via Lefthook / `task hooks:*` on **staged** changes (not a substitute for full review on whole files):

- **GDScript:** `task hooks:gd-review` → `.lefthook/scripts/gd_review_check.py` — existing hygiene plus **numeric literals on newly added lines** (aligned with the GDScript subsection above). Skips paths under `tests/` and `reference_projects/`. Requires a git index (skipped outside a repo).
- **Python (`asset_generation/`):** `task hooks:py-review` → `.lefthook/scripts/py-review.sh` runs **[Ruff](https://docs.astral.sh/ruff/)** with rules from `asset_generation/python/pyproject.toml` (`[tool.ruff.lint]`, currently **E9**, **F**, **I**: runtime/syntax errors, Pyflakes, import sorting). Pre-push also runs `ruff check src tests main.py` before pytest. For **lazy imports** and **magic numbers** in Python, reviewers still apply the policy in the bullets above; GDScript literals remain enforced by `gd_review_check.py`.
