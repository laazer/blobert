from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    python_root: Path = Path(__file__).parent.parent.parent.parent / "python"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
