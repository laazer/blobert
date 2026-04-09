import sys
from unittest.mock import MagicMock

sys.modules.setdefault("fastapi", MagicMock())
sys.modules.setdefault("fastapi.responses", MagicMock())
sys.modules.setdefault("sse_starlette.sse", MagicMock())

from routers.run import _build_command, _guess_output_file


def test_build_command_includes_player_finish_and_hex_color():
    command = _build_command(
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


def test_build_command_includes_enemy_finish_and_hex_for_animated():
    command = _build_command(
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


def test_guess_output_file_points_at_last_variant_index():
    assert _guess_output_file("animated", "spider", 1) == "animated_exports/spider_animated_00.glb"
    assert _guess_output_file("animated", "spider", 3) == "animated_exports/spider_animated_02.glb"
    assert _guess_output_file("player", "blue", 2) == "player_exports/player_slime_blue_01.glb"
    assert _guess_output_file("level", "spike_trap", 4) == "level_exports/spike_trap_03.glb"


def test_guess_output_file_draft_subdir_when_requested():
    assert (
        _guess_output_file("animated", "spider", 1, output_draft=True)
        == "animated_exports/draft/spider_animated_00.glb"
    )
    assert (
        _guess_output_file("player", "blue", 2, output_draft=True)
        == "player_exports/draft/player_slime_blue_01.glb"
    )
    assert (
        _guess_output_file("level", "spike_trap", 4, output_draft=True)
        == "level_exports/draft/spike_trap_03.glb"
    )


def test_build_command_does_not_add_finish_flags_for_level():
    command = _build_command(
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
