from typing import TypedDict


class ConfigDict(TypedDict):
    default: str | None
    "Локация, которая используется, если не указывать"


def get_empty_config_dict() -> ConfigDict:
    return {"default": None}


class LocationDict(TypedDict):
    """Информация о месте"""

    name: str
    latitude: float
    longitude: float


class WeatherDict(TypedDict):
    """Информация о погоде"""

    location_name: str
    current: dict | None
    daily: dict | None
    hourly: dict | None


type LocationDicts = dict[str, LocationDict]
type WeatherDicts = dict[str | tuple, WeatherDict]
