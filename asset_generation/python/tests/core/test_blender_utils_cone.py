"""create_cone wiring (bpy ops + active object)."""

from unittest.mock import MagicMock, patch

from src.core import primitives


def test_create_cone_invokes_primitive_add_and_returns_active() -> None:
    fake_obj = MagicMock(name="cone_obj")
    with patch.object(primitives.bpy.ops.mesh, "primitive_cone_add") as pca:
        with patch.object(primitives.bpy.context, "active_object", fake_obj):
            got = primitives.create_cone(
                location=(1, 2, 3), scale=(0.1, 0.1, 0.2), vertices=4, depth=1.5
            )
    assert got is fake_obj
    pca.assert_called_once()
    call_kw = pca.call_args.kwargs
    assert call_kw["vertices"] == 4
    assert call_kw["depth"] == 1.5
    assert call_kw["location"] == (1, 2, 3)
