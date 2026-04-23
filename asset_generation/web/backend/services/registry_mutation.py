"""Registry mutation-oriented service surface for the FastAPI layer.

Note: most manifest mutation workflows already live in `src.model_registry.service`.
This module exists as the explicit backend-side seam for transport code to import, so
`routers/registry.py` can remain thin without re-embedding domain helpers.
"""
from __future__ import annotations

import importlib


def load_model_registry_service():
    # Import lazily so test seams can replace services.python_bridge at runtime.
    bridge = importlib.import_module("services.python_bridge")
    return bridge.import_asset_module("src.model_registry.service")
