from typing import Literal

from niquests import Response, Session
from niquests.adapters import HTTPAdapter

from wthr.models import (
    CurrentForecast,
    DailyForecast,
    ForecastType,
    HourlyForecast,
    Location,
    LocationDict,
    Weather,
)
from wthr.utils import location_cache_storage


class LocationNotFoundError(Exception):
    """Исключение, возникающее, когда локация не найдена с помощью геокодирования"""

    def __init__(self, msg: str = "Локация не найдена"):
        super().__init__(msg)


class APIClient:
    def __init__(self) -> None:
        self._session: Session = self._create_session()
        self.timeout = (5, 10)

    def _create_session(self) -> Session:
        session = Session()
        session.headers.update(
            {
                "User-Agent": "weather-cli/0.1.0",
                "Accept": "application/json",
                # "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )
        adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=5,
            max_retries=2,
            pool_block=False,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get(self, url: str, params: dict | None = None) -> dict:
        r: Response = self._session.get(url=url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()


class WeatherAPIClient(APIClient):
    def __init__(self) -> None:
        super().__init__()
        self._geocoder_url = "https://nominatim.openstreetmap.org/search"
        self._weather_url = "https://api.open-meteo.com/v1/forecast"

    def get_location(self, location: str) -> Location:

        cache: LocationDict | None = location_cache_storage.get_location(location)
        if cache:
            location_: Location = Location.model_validate(cache)
            return location_

        params: dict = {
            "q": location,
            "format": "json",
            "limit": 1,
        }
        raw_data: dict = self._get(url=self._geocoder_url, params=params)

        if not raw_data:
            raise LocationNotFoundError

        location_data: LocationDict = {
            "name": raw_data[0]["display_name"],
            "latitude": round(float(raw_data[0]["lat"]), 2),
            "longitude": round(float(raw_data[0]["lon"]), 2),
        }

        location_cache_storage.save_location(
            name=location,
            display_name=location_data["name"],
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
        )

        location_ = Location.model_validate(location_data)
        return location_

    def get_weather(
        self,
        location: Location,
        forecast_type: ForecastType = ForecastType.CURRENT,
        days: int = 4,
        hours: int = 12,
        timezone: str = "auto",
        temperature_unit: Literal["celsius", "fahrenheit"] | None = None,
        wind_speed_unit: Literal["kmh", "ms", "mph", "knots"] | None = None,
    ) -> Weather:
        """Универсальный метод для получения погоды

        Args:
            location_data: данные локации
            forecast_type: тип прогноза ("current", "daily", "hourly", "mixed")
            days: количество дней для daily-прогноза (1-16)
            hours: количество часов для hourly-прогноза (1-168)
            timezone: временная зона
            temperature_unit: "celsius" или "fahrenheit"
            wind_speed_unit: "kmh", "ms", "mph", "knots"

        Returns:
            WeatherData: Информация о погоде:
            - для current: {"location": "...", "current": {...}}
            - для daily: {"location": "...", "daily": [{...}, {...}]}
            - для hourly: {"location": "...", "hourly": [{...}, {...}]}
            - для mixed: комбинация всех выше
        """

        params: dict = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": timezone,
            "temperature_unit": temperature_unit,
            "wind_speed_unit": wind_speed_unit,
        }

        if forecast_type in (ForecastType.CURRENT, ForecastType.MIXED):
            params["current"] = CurrentForecast.get_request_fields()

        if forecast_type in (ForecastType.DAILY, ForecastType.MIXED):
            params["daily"] = DailyForecast.get_request_fields()
            params["forecast_days"] = min(max(days, 1), 16)  # от 1 до 16

        if forecast_type in (ForecastType.HOURLY, ForecastType.MIXED):
            params["hourly"] = HourlyForecast.get_request_fields()
            params["forecast_hours"] = min(max(hours, 1), 168)  # от 1 до 168

        raw_data: dict = self._get(self._weather_url, params)

        return self._parse_weather_response(
            raw_data=raw_data,
            forecast_type=forecast_type,
            location_name=location.name,
        )

    def _parse_weather_response(
        self,
        raw_data: dict,
        forecast_type: ForecastType,
        location_name: str,
    ) -> Weather:
        """Преобразует ответ API в удобный формат"""
        result: Weather = Weather(location_name=location_name)

        if (
            forecast_type in (ForecastType.CURRENT, ForecastType.MIXED)
            and "current" in raw_data
        ):
            result.current = CurrentForecast.model_validate(raw_data["current"])

        if (
            forecast_type in (ForecastType.DAILY, ForecastType.MIXED)
            and "daily" in raw_data
        ):
            result.daily = [
                DailyForecast.model_validate(item)
                for item in self._normalize_timeseries(raw_data["daily"])
            ]

        if (
            forecast_type in (ForecastType.HOURLY, ForecastType.MIXED)
            and "hourly" in raw_data
        ):
            result.hourly = [
                HourlyForecast.model_validate(item)
                for item in self._normalize_timeseries(raw_data["hourly"])
            ]

        return result

    def _normalize_timeseries(self, data: dict) -> list[dict]:
        """
        Преобразует почасовые или ежедневные данные в удобный формат

        Было: {"time": [...], "weather_code": [...]}
        Стало: [{"time": ..., "weather_code": ...}, ...]
        """
        if not data or "time" not in data:
            return []

        count = len(data["time"])
        result: list[dict] = []

        for i in range(count):
            item: dict = {}
            for key, values in data.items():
                if isinstance(values, list) and len(values) > i:
                    item[key] = values[i]
            result.append(item)

        return result
