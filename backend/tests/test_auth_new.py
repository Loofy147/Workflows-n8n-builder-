from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, get_db
from app.db.base import Base # Import Base from db.base to ensure models are loaded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function", autouse=True)
def override_db(db_session):
    def get_db_override():
        yield db_session
    app.dependency_overrides[get_db] = get_db_override
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

import os

def test_register_and_login():
    # Register
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 201

    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

def test_protected_route_fail():
    response = client.post("/api/chat/", json={"message": "hello"})
    assert response.status_code == 401 # No token
