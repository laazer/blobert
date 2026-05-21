import logging

from fastapi import APIRouter
from models.responses import MetaEnemiesResponse
from models.responses.meta import EnemyMetaRowResponse
from services.python_bridge import import_asset_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta", tags=["meta"])


def _get_canonical_animation_export_names() -> list[str]:
    """Get animation export names from canonical config module."""
    try:
        config_module = import_asset_module("src.utils.config")
        return [
            config_module.AnimationTypes.get_export_name(name)
            for name in config_module.AnimationTypes.get_all()
        ]
    except ImportError as e:
        logger.warning(
            "meta/animations: fallback to hardcoded names — %s", e, exc_info=True
        )
        # Hardcoded fallback (should match canonical order)
        return [
            "Idle", "Walk", "Attack", "Hit", "Death",
            "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire",
            "DamageIce", "Stunned", "Celebrate", "Taunt",
        ]


def _get_canonical_enemies() -> list[dict[str, str]]:
    """Get enemy slug/label catalog from canonical config module."""
    try:
        config_module = import_asset_module("src.utils.config")
        return config_module.animated_enemies_for_api()
    except ImportError as e:
        logger.warning(
            "meta/enemies: fallback to hardcoded slugs — %s", e, exc_info=True
        )
        # Hardcoded fallback (should match canonical order)
        return [
            {"slug": s, "label": " ".join(part.capitalize() for part in s.split("_"))}
            for s in [
                "spider",
                "slug",
                "imp",
                "spitter",
                "claw_crawler",
                "carapace_husk",
            ]
        ]


@router.get("/enemies", response_model=MetaEnemiesResponse, response_model_exclude_none=True)
async def get_enemies() -> MetaEnemiesResponse:
    """Enemy list + procedural build controls from ``asset_generation/python`` (introspects enemy ClassVars)."""
    try:
        build_options_module = import_asset_module("src.utils.build_options")
        import_asset_module("src.utils.config")

        enemies = _get_canonical_enemies()
        build_controls = build_options_module.animated_build_controls_for_api()
    except ImportError as e:
        logger.warning("meta/enemies: ImportError loading build controls — %s", e, exc_info=True)
        return MetaEnemiesResponse(
            enemies=[
                EnemyMetaRowResponse(slug=row["slug"], label=row["label"])
                for row in _get_canonical_enemies()
            ],
            animated_build_controls={},
            meta_backend="fallback",
            meta_error=f"ImportError: {e}",
        )

    return MetaEnemiesResponse(
        enemies=[
            EnemyMetaRowResponse(slug=row["slug"], label=row["label"]) for row in enemies
        ],
        animated_build_controls=build_controls,
        meta_backend="ok",
    )


@router.get("/animations")
async def get_animations() -> dict[str, list[str]]:
    """Return animation export names from canonical config module."""
    return {"animations": _get_canonical_animation_export_names()}
