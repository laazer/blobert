"""
Managed GLB layout: live root vs ``draft/`` subtree for registry-backed exports.

See ``project_board/specs/registry_draft_live_directory_layout_spec.md``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

DRAFT_SUBDIR: Final[str] = "draft"

_MANAGED_ROOTS: Final[frozenset[str]] = frozenset(
    {"animated_exports", "player_exports", "level_exports"},
)


def parse_managed_glb_relative_path(rel_path: str) -> tuple[str, str, bool] | None:
    """
    Return ``(root, basename, is_currently_under_draft)`` for a single-file GLB path
    under a managed root, else ``None``.
    """
    parts = rel_path.split("/")
    if len(parts) < 2:
        return None
    root = parts[0]
    if root not in _MANAGED_ROOTS:
        return None
    if len(parts) == 2 and parts[1].endswith(".glb"):
        return root, parts[1], False
    if len(parts) == 3 and parts[1] == DRAFT_SUBDIR and parts[2].endswith(".glb"):
        return root, parts[2], True
    return None


def expected_relative_path(root: str, basename: str, *, draft: bool) -> str:
    if draft:
        return f"{root}/{DRAFT_SUBDIR}/{basename}"
    return f"{root}/{basename}"


def _sidecar_names(root: str, glb_stem: str) -> list[str]:
    if root == "animated_exports":
        return [f"{glb_stem}.attacks.json"]
    if root == "player_exports":
        return [f"{glb_stem}.player.json"]
    if root == "level_exports":
        return [f"{glb_stem}.object.json"]
    return []


def relocate_registry_row_assets(python_root: Path, rel_path: str, want_draft: bool) -> tuple[str, bool]:
    """
    Move GLB (+ sidecars) so the relative path matches ``want_draft``.

    Returns ``(new_relative_path, moved_files)``.
    """
    parsed = parse_managed_glb_relative_path(rel_path)
    if parsed is None:
        return rel_path, False
    root, basename, _ = parsed
    target = expected_relative_path(root, basename, draft=want_draft)
    if target == rel_path:
        return rel_path, False

    src_glb = python_root / rel_path
    dst_glb = python_root / target
    stem = Path(basename).stem
    sidecars = _sidecar_names(root, stem)

    if dst_glb.is_file():
        if not src_glb.is_file():
            return target, False
        if src_glb.resolve() == dst_glb.resolve():
            return target, False
        raise ValueError(f"refusing relocate: target glb already exists: {target!r}")

    dst_glb.parent.mkdir(parents=True, exist_ok=True)
    moved_any = False
    if src_glb.is_file():
        os.replace(src_glb, dst_glb)
        moved_any = True

    src_dir = python_root / Path(rel_path).parent
    dst_dir = dst_glb.parent
    for sc in sidecars:
        a = src_dir / sc
        b = dst_dir / sc
        if not a.is_file():
            continue
        if b.is_file() and a.resolve() != b.resolve():
            raise ValueError(f"refusing relocate: sidecar already exists at {sc!r}")
        b.parent.mkdir(parents=True, exist_ok=True)
        os.replace(a, b)
        moved_any = True

    return target, moved_any
