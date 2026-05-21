"""Model registry manifest response models (M902-25 pilot)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

_ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "animated_exports/",
    "exports/",
    "player_exports/",
    "level_exports/",
)


def _path_is_allowlisted(path: str) -> bool:
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    return any(path.startswith(prefix) for prefix in _ALLOWLIST_PREFIXES)


class VersionRowResponse(BaseModel):
    """One version row under a family block."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    id: str = Field(..., description="Stable version identifier within the family.")
    path: str = Field(..., description="Registry-relative GLB path under an allowlisted prefix.")
    draft: bool = Field(..., description="Draft flag; draft rows are not spawn-eligible.")
    in_use: bool = Field(..., description="In-use flag for spawn pool eligibility.")
    name: str | None = Field(default=None, description="Optional display name (max 128 chars).")

    @field_validator("id", "path")
    @classmethod
    def _non_empty_stripped(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped

    @field_validator("path")
    @classmethod
    def _allowlisted_path(cls, value: str) -> str:
        if not _path_is_allowlisted(value):
            raise ValueError(f"path not allowlisted: {value!r}")
        return value

    @field_validator("name")
    @classmethod
    def _name_max_len(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) > 128:
            raise ValueError("name exceeds 128 characters")
        return value


class FamilyBlockResponse(BaseModel):
    """Enemy or player family block with versions and optional slot order."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    versions: list[VersionRowResponse] = Field(
        default_factory=list,
        description="Version rows for this family.",
    )
    slots: list[str] | None = Field(
        default=None,
        description="Ordered slot version ids when present.",
    )

    @field_validator("slots")
    @classmethod
    def _slots_non_empty(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        for entry in value:
            if not isinstance(entry, str) or not entry.strip():
                raise ValueError("slot entries must be non-empty strings")
        return value


class PlayerActiveVisualResponse(BaseModel):
    """Player active visual selection row."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    path: str = Field(..., description="Allowlisted path to the active player visual GLB.")
    draft: bool = Field(..., description="Draft flag for the active visual.")

    @field_validator("path")
    @classmethod
    def _allowlisted_path(cls, value: str) -> str:
        if not _path_is_allowlisted(value.strip()):
            raise ValueError(f"path not allowlisted: {value!r}")
        return value.strip()


class ModelRegistryResponse(BaseModel):
    """Effective model registry manifest (MRVC)."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    schema_version: int = Field(..., ge=1, description="Manifest schema version (>= 1).")
    enemies: dict[str, FamilyBlockResponse] = Field(
        ...,
        description="Enemy families keyed by slug.",
    )
    player: FamilyBlockResponse | None = Field(
        default=None,
        description="Player family block when present.",
    )
    player_active_visual: PlayerActiveVisualResponse | None = Field(
        default=None,
        description="Active player visual row or null.",
    )

    @field_validator("enemies")
    @classmethod
    def _enemy_keys_non_empty(cls, value: dict[str, FamilyBlockResponse]) -> dict[str, FamilyBlockResponse]:
        for key in value:
            if not key.strip():
                raise ValueError("enemy family keys must be non-empty")
        return value
