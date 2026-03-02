import json
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import Generic, Iterator, TypeVar

from wthr.models import (
    ConfigDict,
    LocationDicts,
    WeatherDicts,
)

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
        except (FileNotFoundError, OSError):
            pass
