"""Coverage for managed GLB paths and relocate sidecar moves (registry draft/live layout)."""

from __future__ import annotations

from pathlib import Path

from src.model_registry.path_layout import (
    expected_relative_path,
    parse_managed_glb_relative_path,
    relocate_registry_row_assets,
)


def test_parse_managed_glb_live_and_draft_variants() -> None:
    assert parse_managed_glb_relative_path("animated_exports/spider_00.glb") == (
        "animated_exports",
        "spider_00.glb",
        False,
    )
    assert parse_managed_glb_relative_path("animated_exports/draft/spider_00.glb") == (
        "animated_exports",
        "spider_00.glb",
        True,
    )
    assert parse_managed_glb_relative_path("player_exports/slime.glb") == (
        "player_exports",
        "slime.glb",
        False,
    )
    assert parse_managed_glb_relative_path("level_exports/room.glb") == (
        "level_exports",
        "room.glb",
        False,
    )
    assert parse_managed_glb_relative_path("other/foo.glb") is None
    assert parse_managed_glb_relative_path("animated_exports/onlyone") is None


def test_expected_relative_path_round_trip() -> None:
    assert expected_relative_path("animated_exports", "a.glb", draft=False) == "animated_exports/a.glb"
    assert expected_relative_path("animated_exports", "a.glb", draft=True) == "animated_exports/draft/a.glb"


def test_relocate_animated_moves_glb_and_attack_sidecars(tmp_path: Path) -> None:
    rel = "animated_exports/spider_x.glb"
    (tmp_path / "animated_exports").mkdir(parents=True)
    (tmp_path / rel).write_bytes(b"glb")
    stem = "spider_x"
    (tmp_path / "animated_exports" / f"{stem}.attacks.json").write_bytes(b"{}")
    (tmp_path / "animated_exports" / f"{stem}.build_options.json").write_bytes(b"{}")

    new_rel, moved = relocate_registry_row_assets(tmp_path, rel, want_draft=True)
    assert moved is True
    assert new_rel == "animated_exports/draft/spider_x.glb"
    assert (tmp_path / new_rel).read_bytes() == b"glb"
    assert (tmp_path / "animated_exports" / "draft" / f"{stem}.attacks.json").is_file()
    assert (tmp_path / "animated_exports" / "draft" / f"{stem}.build_options.json").is_file()


def test_relocate_player_moves_player_json_sidecar(tmp_path: Path) -> None:
    rel = "player_exports/slime_blue_00.glb"
    (tmp_path / "player_exports").mkdir(parents=True)
    (tmp_path / rel).write_bytes(b"glb")
    stem = "slime_blue_00"
    (tmp_path / "player_exports" / f"{stem}.player.json").write_bytes(b"{}")

    new_rel, moved = relocate_registry_row_assets(tmp_path, rel, want_draft=True)
    assert moved is True
    assert (tmp_path / "player_exports" / "draft" / f"{stem}.player.json").is_file()


def test_relocate_level_moves_object_json_sidecar(tmp_path: Path) -> None:
    rel = "level_exports/platform_01.glb"
    (tmp_path / "level_exports").mkdir(parents=True)
    (tmp_path / rel).write_bytes(b"glb")
    stem = "platform_01"
    (tmp_path / "level_exports" / f"{stem}.object.json").write_bytes(b"{}")

    new_rel, moved = relocate_registry_row_assets(tmp_path, rel, want_draft=True)
    assert moved is True
    assert (tmp_path / "level_exports" / "draft" / f"{stem}.object.json").is_file()


def test_relocate_noop_when_already_at_target(tmp_path: Path) -> None:
    rel = "animated_exports/draft/x.glb"
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).write_bytes(b"1")
    new_rel, moved = relocate_registry_row_assets(tmp_path, rel, want_draft=True)
    assert moved is False
    assert new_rel == rel
