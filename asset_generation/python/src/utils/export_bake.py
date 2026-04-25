"""Bake helpers for export-time material compatibility."""

from __future__ import annotations

import os
from pathlib import Path


def _find_principled_bsdf(nodes: object) -> object | None:
    for node in nodes:
        if getattr(node, "type", None) == "BSDF_PRINCIPLED":
            return node
        if getattr(node, "bl_idname", "") == "ShaderNodeBsdfPrincipled":
            return node
    return None


def _principled_base_color_socket(bsdf: object) -> object | None:
    socket = bsdf.inputs.get("Base Color")
    if socket is None:
        socket = bsdf.inputs.get("Color")
    return socket


def bake_procedural_stripes_for_export(
    mesh_obj: object | None,
    export_dir: str,
    *,
    image_size: int = 1024,
) -> None:
    """Bake stripe-tagged procedural materials to image textures for glTF export.

    This runs as a best-effort compatibility pass. Any bake failure is logged and
    export continues with the existing material graph.
    """
    if mesh_obj is None:
        return

    try:
        import bpy  # type: ignore[import-not-found]
    except Exception:
        return

    if getattr(mesh_obj, "type", None) != "MESH":
        return
    data = getattr(mesh_obj, "data", None)
    if data is None:
        return
    materials = getattr(data, "materials", None)
    if materials is None:
        return

    stripe_materials = []
    for mat in materials:
        if mat is None:
            continue
        try:
            if bool(mat.get("blobert_stripe_procedural", False)):
                stripe_materials.append(mat)
        except Exception:
            continue
    if not stripe_materials:
        return

    try:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        mesh_obj.select_set(True)
        bpy.context.view_layer.objects.active = mesh_obj
    except Exception as exc:
        print(f"[stripe-bake] unable to prepare bake context: {exc}")
        return

    if not getattr(data, "uv_layers", None):
        try:
            data.uv_layers.new(name="UVMap")
        except Exception as exc:
            print(f"[stripe-bake] unable to create UV layer: {exc}")
            return

    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        return
    original_engine = getattr(scene.render, "engine", None)

    bakes_dir = Path(export_dir) / "bakes"
    os.makedirs(bakes_dir, exist_ok=True)

    try:
        scene.render.engine = "CYCLES"
    except Exception:
        pass

    for mat in stripe_materials:
        nt = getattr(mat, "node_tree", None)
        if nt is None:
            continue
        nodes = nt.nodes
        links = nt.links
        bsdf = _find_principled_bsdf(nodes)
        if bsdf is None:
            continue
        bc_in = _principled_base_color_socket(bsdf)
        if bc_in is None:
            continue

        image_name = f"{mat.name}_stripe_bake"
        try:
            bake_img = bpy.data.images.new(
                image_name,
                width=image_size,
                height=image_size,
                alpha=True,
            )
            bake_img.filepath_raw = str((bakes_dir / f"{image_name}.png").absolute())
            bake_img.file_format = "PNG"
        except Exception as exc:
            print(f"[stripe-bake] image creation failed for {mat.name}: {exc}")
            continue

        bake_target = nodes.new(type="ShaderNodeTexImage")
        bake_target.location = (-300, -300)
        bake_target.image = bake_img
        nodes.active = bake_target

        try:
            bpy.ops.object.bake(
                type="DIFFUSE",
                pass_filter={"COLOR"},
                use_clear=True,
                margin=16,
            )
            bake_img.save()
        except Exception as exc:
            print(f"[stripe-bake] bake failed for {mat.name}: {exc}")
            try:
                nodes.remove(bake_target)
            except Exception:
                pass
            continue

        try:
            for lk in list(bc_in.links):
                links.remove(lk)
            tex = nodes.new(type="ShaderNodeTexImage")
            tex.location = (-450, 200)
            tex.image = bake_img
            tex.interpolation = "Linear"
            tex.extension = "REPEAT"

            uv = nodes.new(type="ShaderNodeUVMap")
            uv.location = (-700, 200)
            links.new(uv.outputs["UV"], tex.inputs["Vector"])
            links.new(tex.outputs["Color"], bc_in)
        except Exception as exc:
            print(f"[stripe-bake] failed to wire baked texture for {mat.name}: {exc}")

    if original_engine is not None:
        try:
            scene.render.engine = original_engine
        except Exception:
            pass
