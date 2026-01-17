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
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wf.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Set templates path for tests
    os.environ["TEMPLATES_DIR"] = "../templates"
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_wf.db"):
        os.remove("./test_wf.db")

def get_token():
    client.post(
        "/api/auth/register",
        json={"email": "wf@example.com", "password": "wfpassword"}
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "wf@example.com", "password": "wfpassword"}
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
