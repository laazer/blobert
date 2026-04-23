import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.python_bridge import import_asset_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta", tags=["meta"])

_ANIMATION_EXPORT_NAMES = [
    "Idle", "Walk", "Attack", "Hit", "Death",
    "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire",
    "DamageIce", "Stunned", "Celebrate", "Taunt",
]

_FALLBACK_SLUGS = [
    "spider",
    "slug",
    "imp",
    "spitter",
    "claw_crawler",
    "carapace_husk",
]


def _fallback_enemies() -> list[dict[str, str]]:
    return [
        {"slug": s, "label": " ".join(part.capitalize() for part in s.split("_"))}
        for s in _FALLBACK_SLUGS
    ]


@router.get("/enemies")
async def get_enemies() -> JSONResponse:
    """Enemy list + procedural build controls from ``asset_generation/python`` (introspects enemy ClassVars)."""
    try:
        build_options_module = import_asset_module("src.utils.build_options")
        config_module = import_asset_module("src.utils.config")

        enemies = config_module.animated_enemies_for_api()
        build_controls = build_options_module.animated_build_controls_for_api()
    except ImportError as e:
        logger.warning("meta/enemies: ImportError loading build controls — %s", e, exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "enemies": _fallback_enemies(),
                "animated_build_controls": {},
                "meta_backend": "fallback",
                "meta_error": f"ImportError: {e}",
            },
        )

    return JSONResponse(
        {
            "enemies": enemies,
            "animated_build_controls": build_controls,
            "meta_backend": "ok",
        }
    )


@router.get("/animations")
async def get_animations() -> JSONResponse:
    return JSONResponse({"animations": _ANIMATION_EXPORT_NAMES})
