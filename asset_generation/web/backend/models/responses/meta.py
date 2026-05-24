"""Meta enemies + build controls response models (M902-25 pilot)."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EnemyMetaRowResponse(BaseModel):
    """Enemy slug and display label."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    slug: str = Field(..., min_length=1, description="Enemy family slug.")
    label: str = Field(..., min_length=1, description="Human-readable enemy label.")


class IntControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["int"] = "int"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    min: int
    max: int
    default: int


class SelectControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["select"] = "select"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    options: list[int]
    default: int
    segmented: bool | None = None
    hint: str | None = None


class FloatControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["float"] = "float"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    min: float
    max: float
    step: float
    default: float
    unit: str | None = None
    hint: str | None = None


class StrControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["str"] = "str"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    default: str


class SelectStrControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["select_str"] = "select_str"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    options: list[str]
    default: str
    segmented: bool | None = None
    hint: str | None = None


class FillPickerControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["fill_picker"] = "fill_picker"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)


class BoolControlResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    type: Literal["bool"] = "bool"
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    default: bool


AnimatedBuildControlDefResponse = Annotated[
    Union[
        IntControlResponse,
        SelectControlResponse,
        FloatControlResponse,
        StrControlResponse,
        SelectStrControlResponse,
        BoolControlResponse,
        FillPickerControlResponse,
    ],
    Field(discriminator="type"),
]


class MetaEnemiesResponse(BaseModel):
    """Enemy catalog and procedural build controls."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    enemies: list[EnemyMetaRowResponse] = Field(
        ...,
        description="Enemy slug/label rows.",
    )
    animated_build_controls: dict[str, list[AnimatedBuildControlDefResponse]] = Field(
        default_factory=dict,
        description="Build control definitions keyed by enemy slug.",
    )
    meta_backend: Literal["ok", "fallback"] = Field(
        ...,
        description="Whether Python introspection succeeded.",
    )
    meta_error: str | None = Field(
        default=None,
        description="Error detail when meta_backend is fallback.",
    )

    @model_validator(mode="after")
    def _meta_error_rules(self) -> MetaEnemiesResponse:
        if self.meta_backend == "fallback":
            if not self.meta_error or not self.meta_error.strip():
                raise ValueError("meta_error required when meta_backend is fallback")
        elif self.meta_error is not None:
            raise ValueError("meta_error must be omitted when meta_backend is ok")
        return self
