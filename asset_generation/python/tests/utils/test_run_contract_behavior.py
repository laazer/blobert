from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from src.utils import run_contract


def test_build_command_preserves_flag_and_count_parity() -> None:
    command = run_contract.build_command(
        cmd="animated",
        enemy="spider",
        count=3,
        description="boss variant",
        difficulty="hard",
        finish="matte",
        hex_color="#112233",
    )

    assert command[:3] == [os.sys.executable, "main.py", "animated"]
    assert "spider" in command
    assert "3" in command
    assert "--description" in command
    assert "--difficulty" in command
    assert "--finish" in command
    assert "--hex-color" in command

    smart_command = run_contract.build_command(
        cmd="smart",
        enemy="spider",
        count=9,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
    )
    assert "9" not in smart_command

    level_command = run_contract.build_command(
        cmd="level",
        enemy="spike_trap",
        count=1,
        description=None,
        difficulty=None,
        finish="matte",
        hex_color="#aabbcc",
    )
    assert "--finish" not in level_command
    assert "--hex-color" not in level_command


def test_prepare_run_environment_sets_draft_and_build_options_only_when_allowed(tmp_path: Path) -> None:
    with patch.dict(os.environ, {"PYTHONPATH": "existing:path"}, clear=False):
        _cmd, env, start_index = run_contract.prepare_run_environment(
            python_root=tmp_path,
            cmd="animated",
            enemy="spider",
            count=1,
            description=None,
            difficulty=None,
            finish=None,
            hex_color=None,
            build_options="  {\"seed\": 7}  ",
            output_draft=True,
            replace_variant_index=None,
        )

    assert start_index == 0
    assert env["BLOBERT_BUILD_OPTIONS_JSON"] == "{\"seed\": 7}"
    assert env["BLOBERT_EXPORT_USE_DRAFT_SUBDIR"] == "1"
    assert str(tmp_path) in env["PYTHONPATH"]
    assert str(tmp_path / "bin") in env["PYTHONPATH"]
    assert str(tmp_path / "src") in env["PYTHONPATH"]

    _cmd, no_build_env, _start = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="stats",
        enemy="spider",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options="   ",
        output_draft=True,
        replace_variant_index=None,
    )
    assert "BLOBERT_BUILD_OPTIONS_JSON" not in no_build_env
    assert "BLOBERT_EXPORT_USE_DRAFT_SUBDIR" not in no_build_env


def test_prepare_run_environment_resolves_auto_and_fixed_variant_indices(tmp_path: Path) -> None:
    animated_dir = tmp_path / "animated_exports"
    player_draft_dir = tmp_path / "player_exports" / "draft"
    animated_dir.mkdir(parents=True)
    player_draft_dir.mkdir(parents=True)
    (animated_dir / "spider_animated_00.glb").write_text("x")
    (animated_dir / "spider_animated_07.glb").write_text("x")
    (animated_dir / "spider_animated_abc.glb").write_text("x")
    (player_draft_dir / "player_slime_blue_03.glb").write_text("x")

    _cmd, animated_env, animated_start = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="animated",
        enemy="spider",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=False,
        replace_variant_index=None,
    )
    assert animated_start == 8
    assert animated_env["BLOBERT_EXPORT_START_INDEX"] == "8"

    _cmd, player_env, player_start = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="player",
        enemy="blue",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=True,
        replace_variant_index=None,
    )
    assert player_start == 4
    assert player_env["BLOBERT_EXPORT_START_INDEX"] == "4"

    _cmd, fixed_env, fixed_start = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="level",
        enemy="spike_trap",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=False,
        replace_variant_index=2,
    )
    assert fixed_start == 2
    assert fixed_env["BLOBERT_EXPORT_START_INDEX"] == "2"


def test_predict_output_file_uses_clamped_count_and_draft_paths() -> None:
    assert (
        run_contract.predict_output_file(
            cmd="animated",
            enemy="spider",
            count=3,
            start_index=5,
            output_draft=True,
        )
        == "animated_exports/draft/spider_animated_07.glb"
    )
    assert (
        run_contract.predict_output_file(
            cmd="player",
            enemy="blue",
            count=0,
            start_index=2,
            output_draft=False,
        )
        == "player_exports/player_slime_blue_02.glb"
    )
    assert (
        run_contract.predict_output_file(
            cmd="test",
            enemy=None,
            count=None,
            start_index=0,
            output_draft=False,
        )
        == "animated_exports/spider_animated_00.glb"
    )
    assert run_contract.predict_output_file(
        cmd="smart",
        enemy=None,
        count=4,
        start_index=0,
        output_draft=False,
    ) is None


def test_build_command_rejects_unknown_command_fail_closed() -> None:
    # CHECKPOINT: conservative assumption is that the shared contract rejects
    # unsupported command values before router transport handling.
    try:
        run_contract.build_command(
            cmd="unknown_command",
            enemy="spider",
            count=1,
            description=None,
            difficulty=None,
            finish=None,
            hex_color=None,
        )
    except ValueError:
        return
    raise AssertionError("unknown commands must fail closed with ValueError")


def test_prepare_environment_ignores_variant_override_for_non_export_commands(tmp_path: Path) -> None:
    _cmd, env, start_index = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="stats",
        enemy="spider",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=True,
        replace_variant_index=7,
    )
    assert start_index == 0
    assert "BLOBERT_EXPORT_START_INDEX" not in env


def test_prepare_environment_start_index_scan_ignores_non_two_digit_suffixes(tmp_path: Path) -> None:
    export_dir = tmp_path / "animated_exports"
    export_dir.mkdir(parents=True)
    (export_dir / "spider_animated_00.glb").write_text("x")
    (export_dir / "spider_animated_09.glb").write_text("x")
    (export_dir / "spider_animated_100.glb").write_text("x")
    (export_dir / "spider_animated_9.glb").write_text("x")
    (export_dir / "spider_animated_ab.glb").write_text("x")
    (export_dir / "slug_animated_98.glb").write_text("x")

    _cmd, env, start_index = run_contract.prepare_run_environment(
        python_root=tmp_path,
        cmd="animated",
        enemy="spider",
        count=1,
        description=None,
        difficulty=None,
        finish=None,
        hex_color=None,
        build_options=None,
        output_draft=False,
        replace_variant_index=None,
    )
    assert start_index == 10
    assert env["BLOBERT_EXPORT_START_INDEX"] == "10"


def test_predict_output_file_clamps_negative_and_handles_missing_enemy() -> None:
    assert (
        run_contract.predict_output_file(
            cmd="level",
            enemy="spike_trap",
            count=-99,
            start_index=6,
            output_draft=False,
        )
        == "level_exports/spike_trap_06.glb"
    )
    assert (
        run_contract.predict_output_file(
            cmd="animated",
            enemy=None,
            count=2,
            start_index=0,
            output_draft=False,
        )
        is None
    )
