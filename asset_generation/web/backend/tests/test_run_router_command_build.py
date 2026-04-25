from pathlib import Path

from routers import run as run_mod


def test_build_command_includes_player_finish_and_hex_color() -> None:
    command = run_mod.run_contract.build_command(
        cmd="player",
        enemy="blue",
        count=1,
        description=None,
        difficulty=None,
        finish="matte",
        hex_color="#112233",
    )
    assert "--finish" in command
    assert "matte" in command
    assert "--hex-color" in command
    assert "#112233" in command


def test_build_command_includes_enemy_finish_and_hex_for_animated() -> None:
    command = run_mod.run_contract.build_command(
        cmd="animated",
        enemy="slug",
        count=1,
        description=None,
        difficulty=None,
        finish="matte",
        hex_color="#112233",
    )
    assert "--finish" in command
    assert "--hex-color" in command


def test_guess_output_file_points_at_last_variant_index() -> None:
    assert run_mod.run_contract.predict_output_file("animated", "spider", 1) == "animated_exports/spider_animated_00.glb"
    assert run_mod.run_contract.predict_output_file("animated", "spider", 3) == "animated_exports/spider_animated_02.glb"
    assert run_mod.run_contract.predict_output_file("player", "blue", 2) == "player_exports/player_slime_blue_01.glb"
    assert run_mod.run_contract.predict_output_file("level", "spike_trap", 4) == "level_exports/spike_trap_03.glb"


def test_guess_output_file_draft_subdir_when_requested() -> None:
    assert (
        run_mod.run_contract.predict_output_file("animated", "spider", 1, output_draft=True)
        == "animated_exports/draft/spider_animated_00.glb"
    )
    assert (
        run_mod.run_contract.predict_output_file("player", "blue", 2, output_draft=True)
        == "player_exports/draft/player_slime_blue_01.glb"
    )
    assert (
        run_mod.run_contract.predict_output_file("level", "spike_trap", 4, output_draft=True)
        == "level_exports/draft/spike_trap_03.glb"
    )


def test_prepare_run_replace_variant_pins_start_index(tmp_path: Path) -> None:
    ad = tmp_path / "animated_exports"
    ad.mkdir(parents=True)
    (ad / "spider_animated_00.glb").write_bytes(b"x")
    (ad / "spider_animated_01.glb").write_bytes(b"x")
    _cmd, env, start = run_mod.run_contract.prepare_run_environment(
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
        replace_variant_index=0,
    )
    assert start == 0
    assert env["BLOBERT_EXPORT_START_INDEX"] == "0"


def test_prepare_run_without_replace_uses_next_free_index(tmp_path: Path) -> None:
    ad = tmp_path / "animated_exports"
    ad.mkdir(parents=True)
    (ad / "spider_animated_00.glb").write_bytes(b"x")
    (ad / "spider_animated_01.glb").write_bytes(b"x")
    _cmd, env, start = run_mod.run_contract.prepare_run_environment(
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
    )
    assert start == 2
    assert env["BLOBERT_EXPORT_START_INDEX"] == "2"


def test_build_command_does_not_add_finish_flags_for_level() -> None:
    command = run_mod.run_contract.build_command(
        cmd="level",
        enemy="spike_trap",
        count=1,
        description=None,
        difficulty=None,
        finish="matte",
        hex_color="#112233",
    )
    assert "--finish" not in command
    assert "--hex-color" not in command
