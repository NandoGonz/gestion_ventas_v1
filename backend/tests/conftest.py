"""Fixtures de integración: base SQLite temporal y usuario administrador de prueba."""
import os

os.environ["APP_ENV"] = "test"
os.environ["APP_JWT_SECRET"] = "test-only-secret-that-is-long-enough-for-hmac"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ISSUER"] = "test-gestion-ventas"
os.environ["JWT_AUDIENCE"] = "test-gestion-ventas-api"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["BOOTSTRAP_ADMIN_NAME"] = "Administrador de Prueba"
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin-test@example.com"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "TestAdminPass123!"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin-test@example.com", "password": "TestAdminPass123!"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
