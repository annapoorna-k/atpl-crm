import os

os.environ.update(
    APP_SECRET="test-secret",
    APP_MODE="local-demo",
    INSTANCE_TYPE="INTERNATIONAL",
    TENANT_KEY="test-workspace",
    DATABASE_URL="sqlite+pysqlite:////tmp/atplcrm-pytest.db",
    POSTGRES_PASSWORD="unused",
    DEMO_PASSWORD="ChangeMe1234",
)

import pytest
from fastapi.testclient import TestClient

from atplcrm.database import Base, engine
from atplcrm.main import app
from atplcrm.seed import seed


@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, email: str = "alex@atplcrm.local") -> str:
    csrf = client.get("/api/v1/session/").json()["csrf"]
    response = client.post(
        "/api/v1/session/",
        json={"username": email, "password": "ChangeMe1234"},
        headers={"X-CSRFToken": csrf},
    )
    assert response.status_code == 200, response.text
    return response.json()["csrf"]
