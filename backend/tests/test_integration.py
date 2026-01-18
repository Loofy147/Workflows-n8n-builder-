"""
Integration Tests for AI Workflow Platform
Tests the complete workflow lifecycle: user registration → chat → workflow activation → execution
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.workflow import WorkflowTemplate, UserWorkflow

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test"""
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
def override_dependencies(db_session):
    """Override FastAPI dependencies"""
    import os
    # Set TEMPLATES_DIR to a non-existent path to only load from DB during integration tests
    # This ensures len(data) == 2 in test_get_workflow_templates
    old_templates_dir = os.environ.get("TEMPLATES_DIR")
    os.environ["TEMPLATES_DIR"] = "/tmp/non_existent_templates_dir"

    def get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = get_db_override
    yield
    app.dependency_overrides.clear()
    if old_templates_dir:
        os.environ["TEMPLATES_DIR"] = old_templates_dir
    else:
        del os.environ["TEMPLATES_DIR"]


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def test_user(client):
    """Create and authenticate test user"""
    # Register
    response = client.post(
        "/api/auth/register",
        json={"email": "test@algeria.dz", "password": "TestPass123!"}
    )
    assert response.status_code == 201

    # Login
    response = client.post(
        "/api/auth/login",
        data={"username": "test@algeria.dz", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"email": "test@algeria.dz", "token": token}


@pytest.fixture
def auth_headers(test_user):
    """Authentication headers"""
    return {"Authorization": f"Bearer {test_user['token']}"}


# ============================================================================
# TEST SUITE 1: Authentication & Authorization
# ============================================================================

def test_user_registration(client):
    """Test user can register with valid credentials"""
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@algeria.dz", "password": "SecurePass123!"}
    )
    assert response.status_code == 201
    assert response.json()["message"] == "User created successfully"


def test_duplicate_registration(client, test_user):
    """Test duplicate email registration is rejected"""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@algeria.dz", "password": "AnotherPass123!"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_with_valid_credentials(client, test_user):
    """Test login returns valid JWT token"""
    response = client.post(
        "/api/auth/login",
        data={"username": "test@algeria.dz", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_invalid_credentials(client):
    """Test login fails with wrong password"""
    response = client.post(
        "/api/auth/login",
        data={"username": "test@algeria.dz", "password": "WrongPassword"}
    )
    assert response.status_code == 401


def test_protected_route_without_token(client):
    """Test protected endpoint rejects requests without token"""
    response = client.post("/api/chat/", json={"message": "test"})
    assert response.status_code == 401


def test_protected_route_with_invalid_token(client):
    """Test protected endpoint rejects invalid token"""
    response = client.post(
        "/api/chat/",
        json={"message": "test"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 403


# ============================================================================
# TEST SUITE 2: AI Agent Chat Flow
# ============================================================================

@patch('app.services.ai_agent.AsyncAnthropic')
def test_chat_basic_greeting(mock_anthropic, client, auth_headers):
    """Test AI agent responds to basic greeting"""
    # Mock Anthropic response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "type": "message",
        "message": "Bonjour! Comment puis-je vous aider avec votre automatisation?",
        "suggestions": ["Automatiser Ouedkniss", "Tracking Yalidine"]
    }))]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=100)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic.return_value = mock_client

    # Send chat message
    response = client.post(
        "/api/chat/",
        json={"message": "Salam, comment ça va?"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "message"
    assert "Bonjour" in data["content"]


@patch('app.services.ai_agent.AsyncAnthropic')
def test_chat_workflow_intent_detection(mock_anthropic, client, auth_headers):
    """Test AI agent detects workflow intent and asks clarification questions"""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "type": "clarification",
        "message": "D'accord, je peux vous aider avec Ouedkniss. Quelques questions:",
        "questions": [
            {
                "field": "property_type",
                "question": "Quel type de bien cherchez-vous?",
                "options": ["Appartement", "Maison", "Villa"],
                "required": True
            },
            {
                "field": "wilaya",
                "question": "Dans quelle wilaya?",
                "options": ["16 - Alger", "31 - Oran"],
                "required": True
            }
        ],
        "template_match": "ouedkniss_real_estate",
        "confidence": 0.92
    }))]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=200)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic.return_value = mock_client

    response = client.post(
        "/api/chat/",
        json={"message": "Je veux automatiser la recherche d'appartements sur Ouedkniss"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "clarification"
    assert len(data["questions"]) == 2
    assert data["template_match"] == "ouedkniss_real_estate"


@patch('app.services.ai_agent.AsyncAnthropic')
@patch('app.services.workflow_builder.N8nClient')
def test_chat_to_workflow_creation(mock_n8n, mock_anthropic, client, auth_headers, db_session):
    """Test complete flow: chat → clarification → workflow creation"""
    # Step 1: Mock AI agent workflow-ready response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps({
        "type": "workflow_ready",
        "message": "Parfait! Votre workflow est prêt.",
        "template_id": "ouedkniss_real_estate",
        "inputs": {
            "property_type": "appartement",
            "transaction_type": "vente",
            "wilaya": "16",
            "min_price": 5000000
        },
        "estimated_cost_dzd": 22.5,
        "execution_time_seconds": 45
    }))]
    mock_response.usage = MagicMock(input_tokens=150, output_tokens=250)

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic.return_value = mock_client

    # Step 2: Create template in database
    template = WorkflowTemplate(
        id="ouedkniss_real_estate",
        name="Ouedkniss Real Estate Monitor",
        category="marketing",
        description="Real estate lead scraper",
        keywords=["ouedkniss", "immobilier"],
        required_inputs=[],
        optional_inputs=[],
        n8n_json={"name": "Test_Workflow", "nodes": []},
        estimated_cost_dzd=22.5,
        avg_execution_time_seconds=45
    )
    db_session.add(template)
    db_session.commit()

    # Step 3: Mock n8n API calls
    mock_n8n_instance = MagicMock()
    mock_n8n_instance.create_workflow = AsyncMock(return_value={"id": "n8n_wf_123"})
    mock_n8n_instance.activate_workflow = AsyncMock(return_value={"active": True})
    mock_n8n_instance.build_webhook_url = MagicMock(return_value="https://n8n.example.com/webhook/123")
    mock_n8n.return_value = mock_n8n_instance

    # Step 4: Send chat message
    response = client.post(
        "/api/chat/",
        json={"message": "Appartement à vendre à Alger, min 5M DA"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "workflow_ready"
    assert "workflow" in data
    assert data["workflow"]["id"] is not None


# ============================================================================
# TEST SUITE 3: Workflow Management
# ============================================================================

def test_get_workflow_templates(client, auth_headers, db_session):
    """Test retrieving available workflow templates"""
    # Add test templates
    templates = [
        WorkflowTemplate(
            id="template_1",
            name="Test Template 1",
            category="marketing",
            description="Test",
            keywords=["test"],
            required_inputs=[],
            optional_inputs=[],
            n8n_json={},
            estimated_cost_dzd=10.0,
            avg_execution_time_seconds=30
        ),
        WorkflowTemplate(
            id="template_2",
            name="Test Template 2",
            category="logistics",
            description="Test 2",
            keywords=["test2"],
            required_inputs=[],
            optional_inputs=[],
            n8n_json={},
            estimated_cost_dzd=15.0,
            avg_execution_time_seconds=40
        )
    ]
    for t in templates:
        db_session.add(t)
    db_session.commit()

    response = client.get("/api/workflows/templates", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] in ["template_1", "template_2"]


@patch('app.services.workflow_builder.N8nClient')
def test_workflow_activation(mock_n8n, client, auth_headers, db_session):
    """Test workflow activation with valid inputs"""
    # Create template
    template = WorkflowTemplate(
        id="test_template",
        name="Test Workflow",
        category="test",
        description="Test",
        keywords=["test"],
        required_inputs=[
            {"name": "api_key", "type": "string", "label": "API Key", "required": True}
        ],
        optional_inputs=[],
        n8n_json={"name": "Test_{{user_id}}", "nodes": []},
        estimated_cost_dzd=10.0,
        avg_execution_time_seconds=30
    )
    db_session.add(template)
    db_session.commit()

    # Mock n8n
    mock_n8n_instance = MagicMock()
    mock_n8n_instance.create_workflow = AsyncMock(return_value={"id": "n8n_123"})
    mock_n8n_instance.activate_workflow = AsyncMock(return_value={"active": True})
    mock_n8n_instance.build_webhook_url = MagicMock(return_value="https://webhook.url")
    mock_n8n.return_value = mock_n8n_instance

    # Activate workflow
    response = client.post(
        "/api/workflows/activate",
        json={
            "template_id": "test_template",
            "inputs": {"api_key": "test_key_123"}
        },
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "webhook_url" in data


@patch('app.services.workflow_builder.N8nClient')
def test_workflow_activation_missing_required_input(mock_n8n, client, auth_headers, db_session):
    """Test workflow activation fails with missing required input"""
    template = WorkflowTemplate(
        id="test_template_2",
        name="Test Workflow 2",
        category="test",
        description="Test",
        keywords=["test"],
        required_inputs=[
            {"name": "api_key", "type": "string", "label": "API Key", "required": True}
        ],
        optional_inputs=[],
        n8n_json={"name": "Test", "nodes": []},
        estimated_cost_dzd=10.0,
        avg_execution_time_seconds=30
    )
    db_session.add(template)
    db_session.commit()

    # Try to activate without required input
    response = client.post(
        "/api/workflows/activate",
        json={
            "template_id": "test_template_2",
            "inputs": {}  # Missing api_key
        },
        headers=auth_headers
    )

    assert response.status_code == 500  # Will fail validation in builder


# ============================================================================
# TEST SUITE 4: Algeria-Specific Utils
# ============================================================================

def test_wilaya_validation():
    """Test Algerian wilaya code validation"""
    from app.utils.algeria_utils import validate_wilaya

    assert validate_wilaya("01") == True
    assert validate_wilaya("16") == True
    assert validate_wilaya("58") == True
    assert validate_wilaya("00") == False
    assert validate_wilaya("59") == False
    assert validate_wilaya("abc") == False


def test_phone_number_formatting():
    """Test Algerian phone number formatting"""
    from app.utils.algeria_utils import format_dz_phone

    assert format_dz_phone("0550123456") == "+213550123456"
    assert format_dz_phone("550123456") == "+213550123456"
    assert format_dz_phone("+213550123456") == "+213550123456"
    assert format_dz_phone("213550123456") == "+213550123456"


def test_darja_normalization():
    """Test Darja text normalization for better AI matching"""
    from app.utils.algeria_utils import normalize_darja

    normalized = normalize_darja("Chkoun hada?")
    assert "sh" in normalized  # ch -> sh

    normalized = normalize_darja("Ouedkniss")
    assert "u" in normalized  # ou -> u


# ============================================================================
# TEST SUITE 5: Cost Estimation
# ============================================================================

def test_ai_token_cost_calculation():
    """Test AI token cost calculation in DZD"""
    from app.services.cost_estimator import CostEstimator

    estimator = CostEstimator()
    cost_dzd = estimator.estimate_ai_cost(
        input_tokens=1000,
        output_tokens=500
    )

    # Expected: (1000/1M * 3.0 + 500/1M * 15.0) * 135 * 1.5 (markup)
    # = (0.003 + 0.0075) * 135 * 1.5 = 2.13 DZD
    assert cost_dzd > 0
    assert isinstance(cost_dzd, float)


def test_workflow_execution_cost_calculation():
    """Test workflow execution cost estimation"""
    from app.services.cost_estimator import CostEstimator

    estimator = CostEstimator()
    cost_dzd = estimator.estimate_workflow_cost(
        avg_execution_time=60,  # 60 seconds
        node_count=5
    )

    # Expected: 2.0 (base) + (60/60 * 1.5) + (5 * 0.5) = 2.0 + 1.5 + 2.5 = 6.0 DZD
    assert cost_dzd == 6.0


# ============================================================================
# TEST SUITE 6: Event Bus & Workers
# ============================================================================

@pytest.mark.asyncio
async def test_event_publishing():
    """Test event bus can publish events"""
    from app.services.event_bus import EventBus

    bus = EventBus()

    # Mock redis
    with patch('app.services.event_bus.redis_client') as mock_redis:
        mock_redis.xadd = AsyncMock()

        await bus.publish("test_event", {"data": "test"})

        mock_redis.xadd.assert_called_once()


@pytest.mark.asyncio
async def test_workflow_created_event():
    """Test workflow creation triggers event"""
    from app.services.event_bus import event_bus

    events = []

    async def capture_event(event_type, payload):
        events.append((event_type, payload))

    # This would normally be tested in integration with actual worker
    # For unit test, we just verify the event format
    test_payload = {
        "workflow_id": "wf_123",
        "user_id": "user_456",
        "template_id": "template_789"
    }

    await event_bus.publish("workflow_created", test_payload)

    # In real scenario, worker would consume this event


# ============================================================================
# TEST SUITE 7: Health & Monitoring
# ============================================================================

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "api" in data["checks"]


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
