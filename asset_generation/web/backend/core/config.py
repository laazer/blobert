from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    python_root: Path = Path(__file__).parent.parent.parent.parent / "python"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]
    # GET /api/run/complete — APMCP-RUN-5
    run_complete_default_max_wait_ms: int = 3_600_000
    run_complete_absolute_max_wait_ms: int = 3_600_000
    run_complete_max_log_bytes: int = 262_144


settings = Settings()
