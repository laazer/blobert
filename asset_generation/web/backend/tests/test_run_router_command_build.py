import sys
from unittest.mock import MagicMock

sys.modules.setdefault("fastapi", MagicMock())
sys.modules.setdefault("fastapi.responses", MagicMock())
sys.modules.setdefault("sse_starlette.sse", MagicMock())

from routers.run import _build_command


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
