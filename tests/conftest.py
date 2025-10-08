# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def reset_database():
    # сбрасываем бд перед каждым тестом
    from app.main import _DB

    _DB["cards"] = []
    yield


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)
