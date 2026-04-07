"""export_naming stems match generator output and ExportConfig.ANIMATED_PATTERN."""

from src.utils.constants import ExportConfig
from src.utils.export_naming import animated_export_stem


def test_animated_stem_matches_export_config_pattern() -> None:
    stem = animated_export_stem("slug", 3)
    full = ExportConfig.ANIMATED_PATTERN.format(enemy_type="slug", variant=3, format="glb")
    assert full == f"{stem}.glb"


def test_prefab_stem_includes_prefab_segment() -> None:
    stem = animated_export_stem("slug", 1, prefab_name="mantis")
    assert stem == "slug_animated_prefab_mantis_01"
