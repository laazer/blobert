"""
Shared fixtures for backend tests.

The backend tests must be run from asset_generation/web/backend/:
    cd asset_generation/web/backend && python -m pytest tests/ -v
"""
import sys
import pathlib

# Ensure the backend package root is on sys.path so `from main import app`
# and `from core.config import settings` resolve correctly when pytest is
# invoked from the backend directory.
_BACKEND_ROOT = pathlib.Path(__file__).parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
