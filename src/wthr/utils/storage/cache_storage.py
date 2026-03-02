from pathlib import Path
from typing import Generic

from platformdirs import user_cache_path

from wthr.models import (
    LocationDict,
    LocationDicts,
    WeatherDicts,
)
from wthr.utils.storage.app_info import APP_NAME, LOCATION_CACHE_FILE_NAME
from wthr.utils.storage.storage import Storage, T


class CacheStorage(Storage[T], Generic[T]):
    def __init__(self, app_name: str, file_name: str) -> None:
        folder_path: Path = user_cache_path(app_name)
        empty_data_example: dict = {}
        super().__init__(
            folder_path=folder_path,
            file_name=file_name,
            empty_data_example=empty_data_example,  # type: ignore
        )


class LocationCacheStorage(CacheStorage[LocationDicts]):
    def get_location(self, name: str) -> LocationDict | None:
        """Найти место в кеше
        Args:
            name (str): название, которое дал пользователь
        :return: Место или None, если не найдено
        :rtype: LocationDict | None
        """
        name = name.lower()
        data: LocationDicts = self.get()
        if name in data:
            return data[name]
        return None

    def save_location(
        self,
        name: str,
        display_name: str,
        latitude: float,
        longitude: float,
    ) -> None:
        """Сохранить место в кеш

        Args:
            name (str): название, которое дал пользователь
            display_name (str): полное название (информация), полученное после парсинга
            latitude (float): широта, будет округлена до сотых
            longitude (float): долгота, будет округлена до сотых
        """

        name = name.lower()
        latitude = round(latitude, 2)
        longitude = round(longitude, 2)

        with self.open_data() as data:
            data[name] = {
                "display_name": display_name,
                "latitude": latitude,
                "longitude": longitude,
            }


class WeatherCacheStorage(CacheStorage[WeatherDicts]): ...


location_cache_storage = LocationCacheStorage(APP_NAME, LOCATION_CACHE_FILE_NAME)
