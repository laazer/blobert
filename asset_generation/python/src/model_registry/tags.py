"""Registry version tag normalization (editor + future Godot manifest reads)."""

from __future__ import annotations

import re
from typing import Any

_MAX_TAG_LEN = 48
_MAX_TAGS = 20
_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def normalize_tag_token(raw: str) -> str | None:
    """Return a canonical tag token or None if invalid."""
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower().replace(" ", "_")
    if not s or len(s) > _MAX_TAG_LEN:
        return None
    if not _TAG_RE.match(s):
        return None
    return s


def canonical_version_tags(family_slug: str, raw_tags: Any) -> list[str]:
    """
    Build deterministic tags for one version row.

    The family slug is always the first tag so every model is tied to its family.
    """
    fam = normalize_tag_token(family_slug)
    if fam is None:
        raise ValueError(f"invalid family slug for tags: {family_slug!r}")

    out: list[str] = [fam]
    seen: set[str] = {fam}

    if raw_tags is None:
        return out
    if not isinstance(raw_tags, list):
        raise ValueError("tags must be an array")

    for i, item in enumerate(raw_tags):
        if not isinstance(item, str):
            raise ValueError(f"tags[{i}] must be a string")
        tok = normalize_tag_token(item)
        if tok is None:
            raise ValueError(f"tags[{i}] invalid: {item!r}")
        if tok in seen:
            continue
        if len(out) >= _MAX_TAGS:
            raise ValueError(f"tags exceeds max count {_MAX_TAGS}")
        seen.add(tok)
        out.append(tok)

    return out
