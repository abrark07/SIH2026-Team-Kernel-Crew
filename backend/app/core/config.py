"""
Application settings loaded from environment variables.

All sensitive values (e.g. FIRMS_MAP_KEY) are loaded here and never
exposed through API responses.  Use `get_settings()` as a cached
singleton so the .env file is read only once.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration — reads from environment / .env file."""

    # ── NASA FIRMS ──────────────────────────────────────────────
    FIRMS_MAP_KEY: str = Field(
        default="",
        description="NASA FIRMS MAP_KEY (keep secret)",
        repr=False,                         # never print in logs
    )
    FIRMS_BASE_URL: str = Field(
        default="https://firms.modaps.eosdis.nasa.gov",
        description="FIRMS API base URL",
    )
    FIRMS_SOURCE: str = Field(
        default="VIIRS_NOAA21_NRT",
        description="FIRMS satellite source identifier",
    )
    FIRMS_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="HTTP timeout for FIRMS API requests (seconds)",
    )

    # ── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    # ── App metadata ────────────────────────────────────────────
    APP_TITLE: str = "Industrial Fire Detection API"
    APP_VERSION: str = "0.1.0"

    # ── helpers ─────────────────────────────────────────────────
    @property
    def cors_origin_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS string into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (read .env once)."""
    return Settings()
