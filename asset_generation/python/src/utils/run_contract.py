from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

ALLOWED_COMMANDS = {"animated", "player", "level", "smart", "stats", "test"}
EXPORT_START_INDEX_ENV = "BLOBERT_EXPORT_START_INDEX"


def is_allowed_command(cmd: str) -> bool:
    return cmd in ALLOWED_COMMANDS


def _next_start_index(export_dir: Path, stem_prefix: str) -> int:
    indices: list[int] = []
    for path in export_dir.glob(f"{stem_prefix}_*.glb"):
        match = re.search(r"_(\d{2})$", path.stem)
        if match:
            indices.append(int(match.group(1)))
    return max(indices) + 1 if indices else 0


def build_command(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    description: Optional[str],
    difficulty: Optional[str],
    finish: Optional[str],
    hex_color: Optional[str],
) -> list[str]:
    if not is_allowed_command(cmd):
        raise ValueError(f"Unknown command: {cmd}")

    parts = [sys.executable, "main.py", cmd]
    if enemy:
        parts.append(enemy)
    if count is not None and cmd not in ("smart", "test"):
        parts.append(str(count))
    if description:
        parts.extend(["--description", description])
    if difficulty:
        parts.extend(["--difficulty", difficulty])
    if cmd in ("player", "animated") and finish:
        parts.extend(["--finish", finish])
    if cmd in ("player", "animated") and hex_color:
        parts.extend(["--hex-color", hex_color])
    return parts


def predict_output_file(
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    *,
    start_index: int = 0,
    output_draft: bool = False,
) -> Optional[str]:
    draft_seg = "draft/" if output_draft else ""
    n = max(1, min(99, int(count) if count is not None else 1))
    last = start_index + n - 1
    if cmd == "animated" and enemy:
        return f"animated_exports/{draft_seg}{enemy}_animated_{last:02d}.glb"
    if cmd == "test":
        return "animated_exports/spider_animated_00.glb"
    if cmd == "player" and enemy:
        return f"player_exports/{draft_seg}player_slime_{enemy}_{last:02d}.glb"
    if cmd == "level" and enemy:
        return f"level_exports/{draft_seg}{enemy}_{last:02d}.glb"
    return None


def prepare_run_environment(
    python_root: Path,
    cmd: str,
    enemy: Optional[str],
    count: Optional[int],
    description: Optional[str],
    difficulty: Optional[str],
    finish: Optional[str],
    hex_color: Optional[str],
    build_options: Optional[str],
    output_draft: bool,
    replace_variant_index: Optional[int] = None,
) -> tuple[list[str], dict[str, str], int]:
    command = build_command(cmd, enemy, count, description, difficulty, finish, hex_color)

    env = os.environ.copy()
    root = str(python_root)
    bin_path = str(python_root / "bin")
    src_path = str(python_root / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        [root, bin_path, src_path] + env.get("PYTHONPATH", "").split(os.pathsep)
    )
    if build_options and str(build_options).strip():
        env["BLOBERT_BUILD_OPTIONS_JSON"] = str(build_options).strip()
    if output_draft and cmd in ("animated", "player", "level"):
        env["BLOBERT_EXPORT_USE_DRAFT_SUBDIR"] = "1"

    start_index = 0
    use_fixed_index = replace_variant_index is not None and cmd in ("animated", "player", "level")
    if use_fixed_index:
        assert replace_variant_index is not None
        start_index = replace_variant_index
        env[EXPORT_START_INDEX_ENV] = str(start_index)
    elif cmd == "animated" and enemy and enemy != "all":
        export_dir = python_root / "animated_exports" / ("draft" if output_draft else "")
        start_index = _next_start_index(export_dir, f"{enemy}_animated")
        env[EXPORT_START_INDEX_ENV] = str(start_index)
    elif cmd == "player" and enemy:
        export_dir = python_root / "player_exports" / ("draft" if output_draft else "")
        start_index = _next_start_index(export_dir, f"player_slime_{enemy}")
        env[EXPORT_START_INDEX_ENV] = str(start_index)

    return command, env, start_index
