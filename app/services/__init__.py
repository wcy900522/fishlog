from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "WeatherService":
        from app.services.weather_service import WeatherService

        return WeatherService
    if name == "LevelService":
        from app.services.level_service import LevelService

        return LevelService
    if name == "ExperienceService":
        from app.services.experience_service import ExperienceService

        return ExperienceService
    if name == "BadgeService":
        from app.services.badge_service import BadgeService

        return BadgeService
    raise AttributeError(f"module 'app.services' has no attribute {name!r}")


__all__ = ["BadgeService", "ExperienceService", "LevelService", "WeatherService"]
