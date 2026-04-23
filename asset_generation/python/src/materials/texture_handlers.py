"""Texture handler registry and material construction helpers."""

from __future__ import annotations

from typing import Callable

import bpy

from src.utils.materials import MaterialCategories

TextureHandler = Callable[..., bpy.types.Material]

_ORGANIC_BASE_COLOR_DETAIL_FAC = 0.12
_TEXTURE_HANDLERS: dict[str, TextureHandler] = {}


def register_handler(texture_type: str, handler: TextureHandler) -> None:
    if not callable(handler):
        raise TypeError(f"Texture handler for '{texture_type}' must be callable")
    _TEXTURE_HANDLERS[str(texture_type)] = handler


def get_handlers() -> dict[str, TextureHandler]:
    return _TEXTURE_HANDLERS


def apply_texture(
    texture_type: str,
    mat: bpy.types.Material,
    nodes: object,
    links: object,
    bsdf: object,
    color: tuple[float, ...],
) -> bpy.types.Material:
    handler = _TEXTURE_HANDLERS.get(texture_type)
    if handler is None:
        return mat
    handler(mat, nodes, links, bsdf, color)
    return mat


def force_principled_value(bsdf: object, input_name: str, value: object) -> None:
    socket = bsdf.inputs.get(input_name)
    if socket is None:
        return
    for link in list(socket.links):
        bsdf.id_data.links.remove(link)
    socket.default_value = value


def create_material(
    name: str,
    color: tuple[float, ...],
    metallic: float = 0.0,
    roughness: float = 0.5,
    alpha: float = 1.0,
    transmission: float = 0.0,
    add_texture: bool = True,
    force_surface: bool = False,
    force_base_color: bool = False,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    bsdf.location = (0, 0)
    output.location = (300, 0)

    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission

    if alpha < 1.0:  # pragma: no cover
        mat.blend_method = "BLEND"
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha

    if add_texture:  # pragma: no cover
        texture_type = MaterialCategories.get_texture_type(name)
        apply_texture(texture_type, mat, nodes, links, bsdf, color)

    if force_base_color:
        force_principled_value(bsdf, "Base Color", color)
    if force_surface:
        force_principled_value(bsdf, "Roughness", roughness)
        force_principled_value(bsdf, "Metallic", metallic)
        force_principled_value(bsdf, "Transmission Weight", transmission)
        force_principled_value(bsdf, "Transmission", transmission)
    return mat


def add_organic_texture(_mat, nodes, links, bsdf, base_color):  # pragma: no cover
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value = 15.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6

    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-200, 0)
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = _ORGANIC_BASE_COLOR_DETAIL_FAC
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


def add_metallic_texture(_mat, _nodes, _links, bsdf, _base_color):
    bsdf.inputs["Metallic"].default_value = 0.9


def add_emissive_texture(_mat, nodes, links, bsdf, base_color):  # pragma: no cover
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, -200)
    dim_color = (base_color[0] * 0.5, base_color[1] * 0.5, base_color[2] * 0.5, 1.0)
    emission.inputs["Color"].default_value = dim_color
    emission.inputs["Strength"].default_value = 1.5

    try:
        mix_shader = nodes.new(type="ShaderNodeMixShader")
        mix_shader.location = (200, 0)
        factor_input = mix_shader.inputs.get("Fac") or mix_shader.inputs.get("Factor")
        if factor_input:
            factor_input.default_value = 0.3
        output = nodes.get("Material Output")
        links.new(bsdf.outputs["BSDF"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])
    except Exception:
        emission.inputs["Strength"].default_value = 0.5
        output = nodes.get("Material Output")
        links.new(emission.outputs["Emission"], output.inputs["Surface"])

    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-400, -200)
    noise.inputs["Scale"].default_value = 25.0
    math_node = nodes.new(type="ShaderNodeMath")
    math_node.location = (-200, -200)
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = 0.5
    links.new(noise.outputs["Fac"], math_node.inputs[0])
    links.new(math_node.outputs["Value"], bsdf.inputs["Emission Strength"])


def add_rocky_texture(_mat, nodes, links, bsdf, base_color):  # pragma: no cover
    noise_large = nodes.new(type="ShaderNodeTexNoise")
    noise_large.location = (-600, 100)
    noise_large.inputs["Scale"].default_value = 8.0
    noise_large.inputs["Detail"].default_value = 6.0

    noise_detail = nodes.new(type="ShaderNodeTexNoise")
    noise_detail.location = (-600, -100)
    noise_detail.inputs["Scale"].default_value = 30.0
    noise_detail.inputs["Detail"].default_value = 12.0

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-400, 0)
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.5

    color_mix = nodes.new(type="ShaderNodeMixRGB")
    color_mix.location = (-200, 0)
    color_mix.blend_type = "MULTIPLY"
    color_mix.inputs["Fac"].default_value = 0.4
    color_mix.inputs["Color1"].default_value = base_color

    links.new(noise_large.outputs["Fac"], mix.inputs["Color1"])
    links.new(noise_detail.outputs["Fac"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], color_mix.inputs["Color2"])
    links.new(color_mix.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9


def add_crystalline_texture(mat, nodes, links, bsdf, base_color):  # pragma: no cover
    bsdf.inputs["Roughness"].default_value = 0.1
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.8
        bsdf.inputs["IOR"].default_value = 1.31
    elif "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.7
        mat.blend_method = "BLEND"

    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-400, 0)
    noise.inputs["Scale"].default_value = 20.0
    noise.inputs["Detail"].default_value = 4.0

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-200, 0)
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.1
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


register_handler("organic", add_organic_texture)
register_handler("metallic", add_metallic_texture)
register_handler("emissive", add_emissive_texture)
register_handler("rocky", add_rocky_texture)
register_handler("crystalline", add_crystalline_texture)
