import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class WeatherService:
    @staticmethod
    async def get_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
        """获取当前天气数据"""
        url = f"{settings.OPEN_METEO_API_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m,pressure_msl",
            "timezone": "Asia/Shanghai"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                current = data.get("current", {})
                return {
                    "temperature": current.get("temperature_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "pressure": current.get("pressure_msl"),
                    "raw_json": data
                }
        except Exception as e:
            return {
                "temperature": None,
                "wind_speed": None,
                "pressure": None,
                "raw_json": {"error": str(e)}
            }
