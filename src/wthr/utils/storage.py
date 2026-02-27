import json
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import Generic, Iterator, TypeVar

import typer

from wthr.models import ConfigDict, get_empty_config_dict

APP_NAME = "wthr"
FILE_NAME = "config.json"


T = TypeVar("T", bound=(dict | ConfigDict))


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

    def set_default_location(self, default_location: str | None):
        with self.open_data() as config:
            config["default"] = default_location

    def get_default_location(self) -> str | None:
        return self.get()["default"]


config_storage = ConfigStorage(APP_NAME, FILE_NAME)
