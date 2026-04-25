"""Shared manifest schema contract - Pydantic models for API, TypedDict for domain."""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class VersionRowTypedDict(TypedDict, total=False):
    """Domain-layer TypedDict for version row (framework-agnostic)."""

    id: str
    path: str
    draft: bool
    in_use: bool
    name: str


class FamilyBlockTypedDict(TypedDict, total=False):
    """Domain-layer TypedDict for family block."""

    versions: list[VersionRowTypedDict]
    slots: list[str]


class ManifestTypedDict(TypedDict):
    """Domain-layer TypedDict for manifest (framework-agnostic)."""

    schema_version: int
    enemies: dict[str, FamilyBlockTypedDict]
    player: FamilyBlockTypedDict
    player_active_visual: dict[str, Any] | None


class VersionRowPydantic(BaseModel):
    """Pydantic model for version row (API payload)."""

    id: str = Field(..., description="Unique version identifier")
    path: str = Field(..., description="Path to asset export")
    draft: bool = Field(..., description="Whether this is a draft version")
    in_use: bool = Field(..., description="Whether this version is currently in use")
    name: str | None = Field(None, max_length=128, description="Human-readable name")


class FamilyBlockPydantic(BaseModel):
    """Pydantic model for family block (API payload)."""

    versions: list[VersionRowPydantic] = Field(..., description="List of version rows")
    slots: list[str] | None = Field(None, description="Slot assignments by version ID")


class ManifestPydantic(BaseModel):
    """Pydantic model for manifest (API payload)."""

    schema_version: int = Field(..., ge=1, description="Schema version number")
    enemies: dict[str, FamilyBlockPydantic] = Field(
        ..., description="Enemy family registry"
    )
    player: FamilyBlockPydantic = Field(..., description="Player asset registry")
    player_active_visual: dict[str, Any] | None = Field(
        None, description="Derived active visual from player block"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "schema_version": 1,
                "enemies": {
                    "adhesion_bug": {
                        "versions": [
                            {
                                "id": "v001",
                                "path": "animated_exports/adhesion_bug_animated_00.glb",
                                "draft": False,
                                "in_use": True,
                                "name": "Adhesion Bug Variant 1",
                            }
                        ],
                        "slots": ["v001"],
                    }
                },
                "player": {
                    "versions": [
                        {"id": "p001", "path": "exports/blobert_default.glb", "draft": False, "in_use": True}
                    ],
                    "slots": ["p001"],
                },
            }
        }


def typeddict_to_pydantic_manifest(manifest: ManifestTypedDict) -> ManifestPydantic:
    """Convert TypedDict manifest to Pydantic model for API validation."""

    def convert_family_block(family: FamilyBlockTypedDict) -> FamilyBlockPydantic:
        versions = [VersionRowPydantic(**v) for v in family.get("versions", [])]  # type: ignore
        slots = family.get("slots")
        return FamilyBlockPydantic(versions=versions, slots=slots)

    enemies = {
        name: convert_family_block(family)
        for name, family in manifest.get("enemies", {}).items()  # type: ignore
    }

    player = convert_family_block(manifest["player"])  # type: ignore

    return ManifestPydantic(
        schema_version=manifest["schema_version"],  # type: ignore
        enemies=enemies,
        player=player,
        player_active_visual=manifest.get("player_active_visual"),  # type: ignore
    )


def pydantic_to_typeddict_manifest(manifest: ManifestPydantic) -> ManifestTypedDict:
    """Convert Pydantic model to TypedDict for domain layer."""

    def convert_family_block_pydantic(family: FamilyBlockPydantic) -> FamilyBlockTypedDict:
        versions = [v.model_dump() for v in family.versions]
        return FamilyBlockTypedDict(versions=versions, slots=family.slots or [])  # type: ignore

    enemies = {name: convert_family_block_pydantic(family) for name, family in manifest.enemies.items()}

    player = convert_family_block_pydantic(manifest.player)

    return ManifestTypedDict(
        schema_version=manifest.schema_version,
        enemies=enemies,  # type: ignore
        player=player,  # type: ignore
        player_active_visual=manifest.player_active_visual,  # type: ignore
    )


__all__ = [
    "ManifestTypedDict",
    "FamilyBlockTypedDict",
    "VersionRowTypedDict",
    "ManifestPydantic",
    "FamilyBlockPydantic",
    "VersionRowPydantic",
    "typeddict_to_pydantic_manifest",
    "pydantic_to_typeddict_manifest",
]
