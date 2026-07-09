from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.weather_service import WeatherService


router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current")
async def get_current_weather(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
):
    weather = await WeatherService.get_current_weather(latitude, longitude)
    return {
        "temperature": weather.get("temperature"),
        "wind_speed": weather.get("wind_speed"),
        "pressure": weather.get("pressure"),
        "humidity": weather.get("humidity"),
        "weather": weather.get("weather"),
        "city": weather.get("city"),
        "source": weather.get("source", "open-meteo"),
    }


@router.get("/geocode")
async def search_locations(
    keyword: str = Query(min_length=1, max_length=120),
    city: str | None = Query(default=None, max_length=50),
):
    return await WeatherService.search_locations(keyword, city=city)
