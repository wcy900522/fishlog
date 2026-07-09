from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class WeatherService:
    @staticmethod
    async def get_current_weather(latitude: float, longitude: float) -> dict[str, Any]:
        """获取当前天气数据。"""
        open_meteo_weather = await WeatherService._get_open_meteo_weather(latitude, longitude)
        if settings.AMAP_WEB_SERVICE_KEY:
            amap_weather = await WeatherService._get_amap_weather(latitude, longitude)
            if not amap_weather.get("raw_json", {}).get("error"):
                amap_weather["wind_speed"] = open_meteo_weather.get("wind_speed")
                amap_weather["pressure"] = open_meteo_weather.get("pressure")
                amap_weather["raw_json"] = {
                    "amap": amap_weather.get("raw_json"),
                    "open_meteo": open_meteo_weather.get("raw_json"),
                }
                return amap_weather

        return open_meteo_weather

    @staticmethod
    async def search_locations(keyword: str, city: str | None = None, limit: int = 8) -> dict[str, Any]:
        """Search map locations, preferring AMap POI search and falling back to geocoding."""
        keyword = (keyword or "").strip()
        if not keyword:
            return {"results": [], "source": None, "search_enabled": False}

        async with httpx.AsyncClient() as client:
            if settings.AMAP_WEB_SERVICE_KEY:
                amap_results = await WeatherService._search_amap_locations(client, keyword, city, limit)
                if amap_results:
                    return {"results": amap_results, "source": "amap", "search_enabled": True}

            fallback_results = await WeatherService._search_openstreetmap_locations(client, keyword, limit)
            return {
                "results": fallback_results,
                "source": "openstreetmap",
                "search_enabled": True,
                "amap_configured": bool(settings.AMAP_WEB_SERVICE_KEY),
            }

    @staticmethod
    async def _search_amap_locations(
        client: httpx.AsyncClient,
        keyword: str,
        city: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for query in WeatherService._location_query_variants(keyword):
            results.extend(await WeatherService._search_amap_pois(client, query, city, limit))
            if len(results) >= limit:
                break
            results.extend(await WeatherService._search_amap_geocodes(client, query, city, limit))
            if len(results) >= limit:
                break

        return WeatherService._dedupe_locations(results)[:limit]

    @staticmethod
    async def _search_amap_pois(
        client: httpx.AsyncClient,
        keyword: str,
        city: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "key": settings.AMAP_WEB_SERVICE_KEY,
            "keywords": keyword,
            "offset": min(limit, 20),
            "page": 1,
            "extensions": "base",
            "citylimit": "false",
            "output": "JSON",
        }
        if city:
            params["city"] = city
        try:
            response = await client.get("https://restapi.amap.com/v3/place/text", params=params, timeout=8.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                return []

            results: list[dict[str, Any]] = []
            for item in data.get("pois", [])[:limit]:
                parsed = WeatherService._parse_location_string(item.get("location"))
                if not parsed:
                    continue
                longitude, latitude = parsed
                results.append({
                    "name": item.get("name") or keyword,
                    "address": item.get("address") if isinstance(item.get("address"), str) else None,
                    "province": item.get("pname") if isinstance(item.get("pname"), str) else None,
                    "city": item.get("cityname") if isinstance(item.get("cityname"), str) else None,
                    "district": item.get("adname") if isinstance(item.get("adname"), str) else None,
                    "latitude": latitude,
                    "longitude": longitude,
                })
            return results
        except Exception:
            return []

    @staticmethod
    async def _search_amap_geocodes(
        client: httpx.AsyncClient,
        keyword: str,
        city: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "key": settings.AMAP_WEB_SERVICE_KEY,
            "address": keyword,
            "output": "JSON",
        }
        if city:
            params["city"] = city
        try:
            response = await client.get("https://restapi.amap.com/v3/geocode/geo", params=params, timeout=8.0)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                return []

            results: list[dict[str, Any]] = []
            for item in data.get("geocodes", [])[:limit]:
                parsed = WeatherService._parse_location_string(item.get("location"))
                if not parsed:
                    continue
                longitude, latitude = parsed
                results.append({
                    "name": item.get("formatted_address") or keyword,
                    "province": item.get("province") if isinstance(item.get("province"), str) else None,
                    "city": item.get("city") if isinstance(item.get("city"), str) else None,
                    "district": item.get("district") if isinstance(item.get("district"), str) else None,
                    "latitude": latitude,
                    "longitude": longitude,
                })
            return results
        except Exception:
            return []

    @staticmethod
    async def _search_openstreetmap_locations(
        client: httpx.AsyncClient,
        keyword: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for query in WeatherService._location_query_variants(keyword):
            try:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "limit": limit,
                        "accept-language": "zh-CN",
                    },
                    headers={"User-Agent": "AnglrLog/1.0"},
                    timeout=httpx.Timeout(3.0, connect=2.0),
                )
                response.raise_for_status()
                data = response.json()
            except Exception:
                continue

            for item in data[:limit]:
                try:
                    latitude = float(item.get("lat"))
                    longitude = float(item.get("lon"))
                except (TypeError, ValueError):
                    continue
                address = item.get("address") if isinstance(item.get("address"), dict) else {}
                results.append({
                    "name": item.get("display_name") or query,
                    "province": address.get("state") or address.get("province"),
                    "city": address.get("city") or address.get("county"),
                    "district": address.get("suburb") or address.get("district"),
                    "latitude": latitude,
                    "longitude": longitude,
                })
            if len(results) >= limit:
                break
        return WeatherService._dedupe_locations(results)[:limit]

    @staticmethod
    def _location_query_variants(keyword: str) -> list[str]:
        variants = [keyword]
        if keyword.startswith("顺义") and "北京" not in keyword:
            tail = keyword.removeprefix("顺义").strip()
            if tail:
                variants.extend([f"北京 顺义 {tail}", f"北京市顺义区{tail}"])
        if "北京" not in keyword and any(part in keyword for part in ("顺义", "通州", "昌平", "房山", "怀柔", "密云", "延庆", "平谷", "大兴", "门头沟")):
            variants.append(f"北京 {keyword}")
        compacted: list[str] = []
        for value in variants:
            if value and value not in compacted:
                compacted.append(value)
        return compacted

    @staticmethod
    def _parse_location_string(location: Any) -> tuple[float, float] | None:
        try:
            longitude_text, latitude_text = str(location or "").split(",", 1)
            return float(longitude_text), float(latitude_text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _dedupe_locations(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        results: list[dict[str, Any]] = []
        for item in locations:
            key = (
                str(item.get("name") or ""),
                f"{float(item.get('latitude', 0)):.6f}",
                f"{float(item.get('longitude', 0)):.6f}",
            )
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
        return results

    @staticmethod
    async def _get_open_meteo_weather(latitude: float, longitude: float) -> dict[str, Any]:
        url = f"{settings.OPEN_METEO_API_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m,pressure_msl",
            "timezone": "Asia/Shanghai",
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
                    "source": "open-meteo",
                    "raw_json": data,
                }
        except Exception as exc:
            return {
                "temperature": None,
                "wind_speed": None,
                "pressure": None,
                "source": "open-meteo",
                "raw_json": {"error": str(exc)},
            }

    @staticmethod
    async def _get_amap_weather(latitude: float, longitude: float) -> dict[str, Any]:
        """通过高德逆地理编码获取 adcode，再查询国内实时天气。"""
        try:
            async with httpx.AsyncClient() as client:
                geo_response = await client.get(
                    "https://restapi.amap.com/v3/geocode/regeo",
                    params={
                        "key": settings.AMAP_WEB_SERVICE_KEY,
                        "location": f"{longitude},{latitude}",
                        "extensions": "base",
                    },
                    timeout=8.0,
                )
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                if geo_data.get("status") != "1":
                    raise ValueError(geo_data.get("info") or "Amap geocode failed")

                component = geo_data.get("regeocode", {}).get("addressComponent", {})
                adcode = component.get("adcode")
                if not adcode:
                    raise ValueError("Amap adcode not found")

                weather_response = await client.get(
                    "https://restapi.amap.com/v3/weather/weatherInfo",
                    params={
                        "key": settings.AMAP_WEB_SERVICE_KEY,
                        "city": adcode,
                        "extensions": "base",
                    },
                    timeout=8.0,
                )
                weather_response.raise_for_status()
                weather_data = weather_response.json()
                if weather_data.get("status") != "1":
                    raise ValueError(weather_data.get("info") or "Amap weather failed")

                live = (weather_data.get("lives") or [{}])[0]
                return {
                    "temperature": WeatherService._number_or_none(live.get("temperature")),
                    "wind_power": live.get("windpower"),
                    "wind_direction": live.get("winddirection"),
                    "humidity": WeatherService._number_or_none(live.get("humidity")),
                    "weather": live.get("weather"),
                    "city": live.get("city") or component.get("city") or component.get("province"),
                    "source": "amap",
                    "raw_json": {
                        "geocode": geo_data,
                        "weather": weather_data,
                    },
                }
        except Exception as exc:
            return {
                "temperature": None,
                "wind_speed": None,
                "pressure": None,
                "humidity": None,
                "weather": None,
                "city": None,
                "source": "amap",
                "raw_json": {"error": str(exc)},
            }

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
