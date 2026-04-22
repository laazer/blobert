"""Registry mutation-oriented service surface for the FastAPI layer.

Note: most manifest mutation workflows already live in `src.model_registry.service`.
This module exists as the explicit backend-side seam for transport code to import, so
`routers/registry.py` can remain thin without re-embedding domain helpers.
"""
from __future__ import annotations

from services.python_bridge import import_asset_module


def load_model_registry_service():
    return import_asset_module("src.model_registry.service")
