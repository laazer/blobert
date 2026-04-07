import sys

from core.config import settings
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/meta", tags=["meta"])

_ANIMATION_EXPORT_NAMES = [
    "Idle", "Walk", "Attack", "Hit", "Death",
    "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire",
    "DamageIce", "Stunned", "Celebrate", "Taunt",
]


@router.get("/enemies")
async def get_enemies() -> JSONResponse:
    # Import ANIMATED_SLUGS from the Python asset generation package
    python_root = str(settings.python_root)
    src_path = str(settings.python_root / "src")
    for p in (python_root, src_path):
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        from utils.animated_build_options import animated_build_controls_for_api
        from utils.enemy_slug_registry import animated_enemies_for_api

        enemies = animated_enemies_for_api()
        build_controls = animated_build_controls_for_api()
    except ImportError:
        # Fallback: slug list + mechanical labels (no registry import)
        _fallback_slugs = [
            "spider",
            "slug",
            "imp",
            "spitter",
            "claw_crawler",
            "carapace_husk",
        ]
        enemies = [
            {"slug": s, "label": " ".join(part.capitalize() for part in s.split("_"))}
            for s in _fallback_slugs
        ]
        build_controls = {}

    return JSONResponse(
        {
            "enemies": enemies,
            "animated_build_controls": build_controls,
        }
    )


@router.get("/animations")
async def get_animations() -> JSONResponse:
    return JSONResponse({"animations": _ANIMATION_EXPORT_NAMES})
