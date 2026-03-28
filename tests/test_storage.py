import json
from pathlib import Path

import pytest

from wthr.database.storage.storage import Storage


@pytest.fixture
def storage(tmp_path: Path) -> Storage[dict]:
    folder_path: Path = tmp_path / "data"
    file_name = "storage.json"
    empty_data_example: dict = {}
    return Storage(folder_path, file_name, empty_data_example)


def test_create_folder(storage: Storage[dict]):
    assert not storage._folder_path.exists()
    storage._create_folder()
    assert storage._folder_path.exists()


def test_get(storage: Storage[dict]):
    test_data = {"test_get": "yes"}

    storage._create_folder()
    with open(storage._file_path, "w") as file:
        json.dump(test_data, file)

    data = storage.get()
    assert data == test_data


def test_get_when_file_not_exist(storage: Storage[dict]):
    data: dict = storage.get()
    assert data == {}
    assert not storage._folder_path.exists()
    assert not storage._file_path.exists()


def test_get_when_json_invalid(storage: Storage[dict]):
    storage._create_folder()
    with open(storage._file_path, "w") as f:
        f.write("invalid json")

    data = storage.get()
    assert data == {}


def test_open_data_creates_folder_and_file(storage: Storage[dict]):
    with storage.open_data() as data:
        assert data == {}
        data["new"] = 123

    assert storage._file_path.exists()
    with open(storage._file_path) as file:
        saved = json.load(file)
    assert saved == {"new": 123}


def test_open_data_loads_existing_data(storage: Storage[dict]):
    storage._create_folder()
    init = {"key": "init"}
    with open(storage._file_path, "w") as f:
        json.dump(init, f)

    with storage.open_data() as data:
        assert data == init
        data["key"] = "new"

    with open(storage._file_path) as f:
        saved = json.load(f)
    assert saved == {"key": "new"}


def test_open_data_and_get(storage: Storage[dict]):
    with storage.open_data() as data:
        data["drink"] = "beer"
        data[42] = 52

    assert storage.get() == {"drink": "beer", "42": 52}


def test_clear_removes_file_and_folder_when_empty(storage):
    storage._create_folder()
    with storage.open_data() as data:
        data["hello"] = "world"

    assert storage._folder_path.exists()
    assert storage._file_path.exists()
    storage.clear()
    assert not storage._folder_path.exists()
    assert not storage._file_path.exists()
