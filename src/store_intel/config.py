"""
Application configuration via pydantic-settings.

Reads from environment variables and .env files.
All settings are centralized here — no magic strings scattered across modules.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Global application settings."""

    # ── Application ─────────────────────────────────────────
    app_name: str = "Store Intelligence System"
    version: str = "0.1.0"
    environment: str = Field(default="development", description="development | staging | production")
    debug: bool = False

    # ── Database ────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///data/store_intel.db",
        description="SQLAlchemy database URL",
    )

    # ── Logging ─────────────────────────────────────────────
    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    # ── Detection Pipeline ──────────────────────────────────
    # TODO: Add detection-related settings when pipeline is implemented
    # target_fps: int = 5
    # detection_confidence: float = 0.45
    # tracker_lost_buffer: int = 30

    # ── Business Rules ──────────────────────────────────────
    # TODO: Add business rule thresholds when analytics are implemented
    # reentry_window_seconds: int = 300
    # staff_dwell_threshold_seconds: int = 3600
    # transaction_dwell_threshold_seconds: int = 30
    # max_queue_depth: int = 8
    # empty_store_threshold_minutes: int = 30
    # abandonment_rate_threshold: float = 0.4
    # max_zone_dwell_minutes: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance — import this everywhere
settings = Settings()
