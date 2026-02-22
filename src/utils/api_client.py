from enum import Enum
from typing import Literal, NotRequired, TypedDict

from niquests import Response, Session
from niquests.adapters import HTTPAdapter


class LocationData(TypedDict):
    """Информация о месте"""

    location: str
    latitude: float
    longitude: float


class WeatherData(TypedDict):
    """Информация о погоде"""

    location: str
    current: NotRequired[dict]
    daily: NotRequired[list[dict]]
    hourly: NotRequired[list[dict]]


class ForecastType(str, Enum):
    """Тип прогноза"""

    CURRENT = "current"
    DAILY = "daily"
    HOURLY = "hourly"
    MIXED = "mixed"


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
        self.session.close()


class WeatherAPIClient(APIClient):
    def __init__(self) -> None:
        super().__init__()
        self._geocoder_url = "https://nominatim.openstreetmap.org/search"
        self._weather_url = "https://api.open-meteo.com/v1/forecast"

    def get_location(self, location: str) -> LocationData:
        params: dict = {
            "q": location,
            "format": "json",
            "limit": 1,
        }
        raw_data: dict = self._get(url=self._geocoder_url, params=params)

        if not raw_data:
            raise Exception("Указана неверная локация")  # TODO

        location_data: LocationData = {
            "location": raw_data[0]["display_name"],
            "latitude": float(raw_data[0]["lat"]),
            "longitude": float(raw_data[0]["lon"]),
        }
        return location_data

    def get_weather(
        self,
        location_data: LocationData,
        forecast_type: ForecastType = ForecastType.CURRENT,
        days: int = 1,
        hours: int = 24,
        timezone: str = "auto",
        temperature_unit: Literal["celsius", "fahrenheit"] | None = None,
        wind_speed_unit: Literal["kmh", "ms", "mph", "knots"] | None = None,
    ) -> WeatherData:
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
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
            "timezone": timezone,
            "temperature_unit": temperature_unit,
            "wind_speed_unit": wind_speed_unit,
        }

        if forecast_type in (ForecastType.CURRENT, ForecastType.MIXED):
            params["current"] = [
                "weather_code",
                # температура
                "temperature_2m",
                "apparent_temperature",
                # ветер
                "wind_speed_10m",
                "wind_direction_10m",
                # влажность
                "relative_humidity_2m",
                # день ли
                "is_day",
            ]

        if forecast_type in (ForecastType.DAILY, ForecastType.MIXED):
            params["daily"] = [
                "weather_code",
                # температура
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                # ветер
                "wind_speed_10m_max",
                # восход и закат
                "sunrise",
                "sunset",
                # осадки
                "precipitation_probability_max",
                "precipitation_sum",
            ]
            params["forecast_days"] = min(max(days, 1), 16)  # от 1 до 16

        if forecast_type in (ForecastType.HOURLY, ForecastType.MIXED):
            params["hourly"] = [
                "weather_code",
                # температура
                "temperature_2m",
                "apparent_temperature",
                # ветер
                "wind_speed_10m",
                # влажность
                "relative_humidity_2m",
                # вероятность осадков
                "precipitation_probability",
            ]
            params["forecast_hours"] = min(max(hours, 1), 168)  # от 1 до 168

        raw_data: dict = self._get(self._weather_url, params)

        return self._normalize_response(
            raw_data=raw_data,
            forecast_type=forecast_type,
            location=location_data.get("location", "Unknown"),
        )

    def _normalize_response(
        self,
        raw_data: dict,
        forecast_type: ForecastType,
        location: str,
    ) -> WeatherData:
        """Преобразует ответ API в удобный формат"""
        result: WeatherData = {"location": location}

        if (
            forecast_type in (ForecastType.CURRENT, ForecastType.MIXED)
            and "current" in raw_data
        ):
            result["current"] = raw_data["current"]

        if (
            forecast_type in (ForecastType.DAILY, ForecastType.MIXED)
            and "daily" in raw_data
        ):
            result["daily"] = self._normalize_timeseries(raw_data["daily"])

        if (
            forecast_type in (ForecastType.HOURLY, ForecastType.MIXED)
            and "hourly" in raw_data
        ):
            result["hourly"] = self._normalize_timeseries(raw_data["hourly"])

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


def main() -> None:
    with WeatherAPIClient() as client:
        location: LocationData = client.get_location("Moscow")
        weather: WeatherData = client.get_weather(location, ForecastType.MIXED, 1, 1)

    print(weather)


if __name__ == "__main__":
    main()
