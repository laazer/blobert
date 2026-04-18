"""Shared utilities for Blender GLB gradient texture testing."""

from __future__ import annotations

import json
import struct
import zlib


def align4(n: int) -> int:
    return (n + 3) & ~3


def parse_glb(data: bytes) -> tuple[dict[str, object], bytes]:
    assert data[:4] == b"glTF", "not a GLB"
    pos = 12
    json_obj: dict[str, object] | None = None
    bin_chunk = b""
    while pos < len(data):
        clen = struct.unpack_from("<I", data, pos)[0]
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + clen]
        pos = align4(pos + 8 + clen)
        if ctype == b"JSON":
            json_obj = json.loads(chunk.decode("utf-8"))
        elif ctype == b"BIN\x00":
            bin_chunk = chunk
    assert json_obj is not None
    return json_obj, bin_chunk


def png_histogram(png_bytes: bytes) -> tuple[int, int, int]:
    """Return (max_r, max_g, max_b) from PNG IDAT chunk."""
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = 0
    color_type = 0
    idat_parts: list[bytes] = []
    while pos < len(png_bytes):
        length = struct.unpack(">I", png_bytes[pos : pos + 4])[0]
        chunk_type = png_bytes[pos + 4 : pos + 8]
        chunk_data = png_bytes[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, _bd, color_type, _c, _f, _i = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break
    raw = zlib.decompress(b"".join(idat_parts))
    if color_type == 2:
        bpp = 3
    elif color_type == 6:
        bpp = 4
    else:
        raise AssertionError(f"unsupported PNG color_type {color_type}")
    stride = width * bpp
    max_r = max_g = max_b = 0
    offset = 0
    for _ in range(height):
        ftype = raw[offset]
        offset += 1
        line = raw[offset : offset + stride]
        offset += stride
        assert ftype == 0, f"unsupported PNG filter {ftype}"
        for i in range(0, stride, bpp):
            r, g, b = line[i], line[i + 1], line[i + 2]
            max_r = max(max_r, r)
            max_g = max(max_g, g)
            max_b = max(max_b, b)
    return max_r, max_g, max_b


def first_image_png_from_glb(glb_json: dict[str, object], bin_data: bytes) -> bytes:
    images = glb_json.get("images")
    assert isinstance(images, list) and len(images) > 0
    im0 = images[0]
    assert isinstance(im0, dict)
    bv_idx = im0.get("bufferView")
    assert isinstance(bv_idx, int)
    buf_views = glb_json.get("bufferViews")
    assert isinstance(buf_views, list)
    bv = buf_views[bv_idx]
    assert isinstance(bv, dict)
    offset = int(bv.get("byteOffset", 0))
    length = int(bv["byteLength"])
    png_slice = bin_data[offset : offset + length]
    assert png_slice[:8] == b"\x89PNG\r\n\x1a\n"
    return png_slice
