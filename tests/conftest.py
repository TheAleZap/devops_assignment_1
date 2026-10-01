import pytest

import config
from scheduling import repository as scheduling_repository
from trips import repository as trips_repository


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))
    scheduling_repository.create_tables()
    trips_repository.create_tables()
    yield
