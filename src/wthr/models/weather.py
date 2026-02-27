from typing import Optional, TypedDict

from pydantic import BaseModel, Field

from .forecast import CurrentForecast, DailyForecast, HourlyForecast


class Weather(BaseModel):
    """Информация о погоде"""

    location_name: str = Field(default="Unknown")
    current: Optional[CurrentForecast] = Field(default=None)
    daily: Optional[list[DailyForecast]] = Field(default=None)
    hourly: Optional[list[HourlyForecast]] = Field(default=None)


class WeatherDict(TypedDict):
    """Информация о погоде в виде словаря"""

    location_name: str
    current: dict | None
    daily: dict | None
    hourly: dict | None


type WeatherDicts = dict[str | tuple, WeatherDict]
