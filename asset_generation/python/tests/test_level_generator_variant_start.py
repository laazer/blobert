"""``generate_level_object`` honors ``BLOBERT_EXPORT_START_INDEX`` (regenerate / pinned variant)."""

import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("bpy", MagicMock())
sys.modules.setdefault("bmesh", MagicMock())
sys.modules.setdefault("mathutils", MagicMock())

import pytest

from src.level_generator import generate_level_object


def test_generate_level_object_offsets_variant_from_env_start(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("BLOBERT_EXPORT_START_INDEX", "3")
    export_dir = str(tmp_path)
    with (
        patch("src.level_generator.clear_scene"),
        patch("src.level_generator.setup_scene"),
        patch(
            "src.level_generator.LevelObjectBuilder.export",
            return_value=str(tmp_path / "out.glb"),
        ) as mock_export,
    ):
        generate_level_object("spike_trap", count=2, seed=1, export_dir=export_dir)
    assert mock_export.call_count == 2
    assert mock_export.call_args_list[0].kwargs["variant_index"] == 3
    assert mock_export.call_args_list[1].kwargs["variant_index"] == 4
