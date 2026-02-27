import json
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import Generic, Iterator, TypeVar

import typer
from platformdirs import user_cache_path

from wthr.models import (
    ConfigDict,
    LocationDict,
    LocationDicts,
    WeatherDicts,
    get_empty_config_dict,
)

APP_NAME = "wthr"
CONFIG_FILE_NAME = "config.json"
LOCATION_CACHE_FILE_NAME = "location.json"


T = TypeVar("T", bound=(dict | ConfigDict | LocationDicts | WeatherDicts))


class Storage(ABC, Generic[T]):
    def __init__(
        self, folder_path: Path, file_name: str, empty_data_example: T
    ) -> None:
        self._folder_path: Path = folder_path
        self._file_path: Path = folder_path / file_name
        self._empty_data_example: T = empty_data_example

    def _create_folder(self) -> None:
        self._folder_path.mkdir(exist_ok=True, parents=True)

    def get(self) -> T:
        """Получить все данные из хранилища

        Returns:
            T (dict): словарь в зависимости от типа хранилища
        """
        try:
            with open(self._file_path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return self._empty_data_example

    @contextmanager
    def open_data(self) -> Iterator[T]:
        """Контекстный менеджер, который возвращает изменяемый объект, который будет сохранен в хранилище"""
        self._create_folder()
        try:
            with open(self._file_path, "r") as file:
                data: T = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            data = self._empty_data_example
        yield data
        with open(self._file_path, "w") as file:
            json.dump(data, file)

    def clear(self) -> None:
        """Удаляет папку и файл, которые использовались, как хранилище"""
        self._file_path.unlink(missing_ok=True)
        try:
            self._folder_path.rmdir()
        except FileNotFoundError:
            pass


class ConfigStorage(Storage[ConfigDict]):
    def __init__(self, app_name: str, file_name: str) -> None:
        folder_path = Path(typer.get_app_dir(app_name))
        empty_data_example: ConfigDict = get_empty_config_dict()
        super().__init__(
            folder_path=folder_path,
            file_name=file_name,
            empty_data_example=empty_data_example,
        )

    def set_default_location(self, default_location: str | None) -> None:
        """Сохранить место по умолчанию"""
        with self.open_data() as config:
            config["default"] = default_location

    def get_default_location(self) -> str | None:
        """Получить место по умолчанию"""
        return self.get()["default"]


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


config_storage = ConfigStorage(APP_NAME, CONFIG_FILE_NAME)
location_cache_storage = LocationCacheStorage(APP_NAME, LOCATION_CACHE_FILE_NAME)
