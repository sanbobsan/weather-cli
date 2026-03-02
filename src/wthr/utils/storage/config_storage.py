from pathlib import Path

import typer

from wthr.models import (
    ConfigDict,
    get_empty_config_dict,
)
from wthr.utils.storage.app_info import APP_NAME, CONFIG_FILE_NAME
from wthr.utils.storage.storage import Storage


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


config_storage = ConfigStorage(APP_NAME, CONFIG_FILE_NAME)
