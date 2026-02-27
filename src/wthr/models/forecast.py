from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ForecastType(str, Enum):
    """Тип прогноза"""

    CURRENT = "current"
    DAILY = "daily"
    HOURLY = "hourly"
    MIXED = "mixed"


class ForecastModel(BaseModel, ABC):
    """
    Базовая модель погоды.
    Содержит поля, которые есть в Current, Daily и Hourly
    """

    time: datetime = Field()
    weather_code: int = Field(alias="weather_code")

    @classmethod
    def get_request_fields(cls) -> list[str]:
        """Возвращает список имен полей для использования в запросе, пропускает поля без alias"""
        return [field.alias for field in cls.model_fields.values() if field.alias]


class CurrentForecast(ForecastModel):
    """Модель текущей погоды"""

    # Температура
    temperature: float = Field(alias="temperature_2m")
    apparent_temperature: Optional[float] = Field(
        default=None, alias="apparent_temperature"
    )
    # Ветер
    wind_speed: float = Field(alias="wind_speed_10m")
    wind_direction: Optional[int] = Field(default=None, alias="wind_direction_10m")
    # Влажность
    relative_humidity: int = Field(alias="relative_humidity_2m")
    # Время суток
    is_day: Literal[0, 1] = Field(alias="is_day")


class DailyForecast(ForecastModel):
    """Модель прогноза по дням"""

    # Температура (мин/макс за день)
    temperature_max: float = Field(alias="temperature_2m_max")
    temperature_min: float = Field(alias="temperature_2m_min")
    apparent_temperature_max: Optional[float] = Field(
        default=None, alias="apparent_temperature_max"
    )
    apparent_temperature_min: Optional[float] = Field(
        default=None, alias="apparent_temperature_min"
    )
    # Ветер (максимальный за день)
    wind_speed_max: Optional[float] = Field(default=None, alias="wind_speed_10m_max")
    # Осадки
    precipitation_probability_max: int = Field(alias="precipitation_probability_max")
    precipitation_sum: Optional[float] = Field(default=None, alias="precipitation_sum")
    # Солнце
    sunrise: datetime = Field(alias="sunrise")
    sunset: datetime = Field(alias="sunset")


class HourlyForecast(ForecastModel):
    """Модель почасового прогноза"""

    # Температура
    temperature: float = Field(alias="temperature_2m")
    apparent_temperature: Optional[float] = Field(
        default=None, alias="apparent_temperature"
    )
    # Ветер
    wind_speed: Optional[float] = Field(default=None, alias="wind_speed_10m")
    # Влажность
    relative_humidity: Optional[int] = Field(default=None, alias="relative_humidity_2m")
    # Осадки
    precipitation_probability: Optional[int] = Field(
        default=None, alias="precipitation_probability"
    )
    # Облачность
    cloud_cover: Optional[int] = Field(default=None, alias="cloud_cover")
