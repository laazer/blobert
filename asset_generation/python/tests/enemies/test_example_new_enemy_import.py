"""Reference template module must import under root conftest bpy stubs (CI / diff-cover)."""


def test_example_new_enemy_module_importable() -> None:
    from src.enemies import example_new_enemy as _mod

    assert _mod.__doc__ and "Examples" in _mod.__doc__
