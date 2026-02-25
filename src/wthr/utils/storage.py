import json
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, TypedDict

import typer

APP_NAME = "wthr"
FILE_NAME = "config.json"


class Config(TypedDict):
    default: str | None
    "Локация, которая используется, если не указывать"


class Storage:
    def __init__(self, app_name: str, file_name: str) -> None:
        self._app_dir = Path(typer.get_app_dir(app_name))
        self._app_dir.mkdir(exist_ok=True, parents=True)

        self._file_path: Path = self._app_dir / file_name

    @contextmanager
    def open_config(self) -> Generator[Config, None, None]:
        try:
            with open(self._file_path, "r") as file:
                data: Config = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {"default": None}
        yield data
        with open(self._file_path, "w") as file:
            json.dump(data, file)

    def _get(self) -> Config:
        try:
            with open(self._file_path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"default": None}

    def set_default_location(self, default_location: str | None):
        with self.open_config() as config:
            config["default"] = default_location

    def get_default_location(self) -> str | None:
        return self._get()["default"]


storage = Storage(APP_NAME, FILE_NAME)
