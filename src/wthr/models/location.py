from typing import TypedDict

from pydantic import BaseModel


class Location(BaseModel):
    """Информация о месте"""

    display_name: str
    latitude: float
    longitude: float


class LocationDict(TypedDict):
    """Информация о месте в виде словаря"""

    display_name: str
    latitude: float
    longitude: float


type LocationDicts = dict[str, LocationDict]
