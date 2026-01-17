from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.db.base import Base # Import Base from db.base to ensure models are loaded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
from unittest.mock import MagicMock, patch

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    # Set templates path for tests
    os.environ["TEMPLATES_DIR"] = "../templates"

    # For in-memory sqlite, we must use a single connection to keep the data alive
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(bind=connection)

    # Update session to use this connection
    old_bind = TestingSessionLocal.kw['bind']
    TestingSessionLocal.configure(bind=connection)

    yield

    transaction.rollback()
    connection.close()
    TestingSessionLocal.configure(bind=old_bind)

def get_token(scopes=None):
    client.post(
        "/api/auth/register",
        json={"email": f"wf_{scopes}@example.com", "password": "wfpassword"}
    )

    # Mocking create_access_token to include scopes in login if we want
    # But simpler is to update auth_utils default or handle it in login.
    # For tests, we'll just mock the dependency get_current_user or update the token logic.

    response = client.post(
        "/api/auth/login",
        data={"username": f"wf_{scopes}@example.com", "password": "wfpassword"}
    )
    return response.json()["access_token"]

def test_get_templates():
    token = get_token()
    response = client.get(
        "/api/workflows/templates",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

@patch("app.services.n8n_client.N8nClient.create_workflow")
@patch("app.services.n8n_client.N8nClient.activate_workflow")
def test_activate_workflow(mock_activate, mock_create):
    mock_create.return_value = {"id": "n8n_wf_123"}
    mock_activate.return_value = {"active": True}

    token = get_token()
    response = client.post(
        "/api/workflows/activate",
        json={
            "template_id": "ouedkniss_lead_gen",
            "inputs": {"keywords": "cars", "wilaya": "16"}
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "webhook_url" in data
