from typing import TypedDict


class ConfigDict(TypedDict):
    default: str | None
    """Локация, которая используется, если не указывать"""


def get_empty_config_dict() -> ConfigDict:
    return {"default": None}
