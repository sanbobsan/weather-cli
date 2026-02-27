from typing import TypedDict

from pydantic import BaseModel


class Location(BaseModel):
    """Информация о месте"""

    name: str
    latitude: float
    longitude: float


class LocationDict(TypedDict):
    """Информация о месте в виде словаря"""

    name: str
    latitude: float
    longitude: float


type LocationDicts = dict[str, LocationDict]
