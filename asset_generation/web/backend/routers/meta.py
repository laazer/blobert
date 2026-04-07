import sys
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.config import settings

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
        from utils.enemy_slug_registry import ANIMATED_SLUGS
        slugs = list(ANIMATED_SLUGS)
    except ImportError:
        # Fallback hardcoded list
        slugs = [
            "adhesion_bug", "tar_slug", "ember_imp",
            "acid_spitter", "claw_crawler", "carapace_husk",
        ]

    return JSONResponse({"enemies": slugs})


@router.get("/animations")
async def get_animations() -> JSONResponse:
    return JSONResponse({"animations": _ANIMATION_EXPORT_NAMES})
