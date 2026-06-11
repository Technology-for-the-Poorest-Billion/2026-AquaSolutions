"""Pytest fixtures.

Each test gets its own fresh SQLite DB at a tempfile path. The Flask
app reads DATABASE_URL from os.environ via engine.get_engine().
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def tmp_db_path(monkeypatch):
    """Per-test scratch SQLite DB. The engine module's cached engine is
    reset so the next get_engine() picks up the new URL."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("MEDICAL_PASSWORD", "med-pw")
    monkeypatch.setenv("GOV_PASSWORD", "gov-pw")
    monkeypatch.setenv("DEVICE_SECRET", "test-device-secret")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")

    # Drop any cached engine from a previous test so the new URL is honoured.
    sys.modules.pop("engine", None)

    yield path
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture()
def app(tmp_db_path):
    """Fresh Flask app bound to the scratch DB. Re-imports so module
    state (DEMO_USERS, init_db, the engine singleton) is rebuilt."""
    for mod in ("app", "database", "labels", "sensor_ingest", "engine"):
        sys.modules.pop(mod, None)
    import app as app_mod
    return app_mod.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def gov_session(client):
    client.post("/login", data={"username": "official.jones", "password": "gov-pw"})
    return client


@pytest.fixture()
def med_session(client):
    client.post("/login", data={"username": "dr.smith", "password": "med-pw"})
    return client