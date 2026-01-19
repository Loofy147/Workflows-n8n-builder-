import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.orchestrator import AgentOrchestrator

@pytest.mark.asyncio
@patch("app.services.orchestrator.AsyncAnthropic")
async def test_orchestrator_routing(mock_anthropic):
    # Mock LLM response for intent analysis
    mock_client = AsyncMock()

    def create_mock_response(text):
        res = MagicMock()
        res.content = [MagicMock(text=text)]
        return res

    mock_client.messages.create = AsyncMock(side_effect=[
        create_mock_response("sales"),
        create_mock_response("logistics"),
        create_mock_response("finance")
    ])
    mock_anthropic.return_value = mock_client

    orchestrator = AgentOrchestrator()

    # Test Sales Routing
    route = await orchestrator._route_request(MagicMock(query="I want to scrape ouedkniss"))
    assert route == "sales"

    # Test Logistics Routing
    route = await orchestrator._route_request(MagicMock(query="How is my yalidine delivery?"))
    assert route == "logistics"

    # Test Finance Routing
    route = await orchestrator._route_request(MagicMock(query="Pay my Baridimob invoice"))
    assert route == "finance"

@pytest.mark.asyncio
@patch("app.services.orchestrator.AsyncAnthropic")
@patch("app.services.ai_agent.AIWorkflowAgent.process_message")
async def test_orchestrator_run(mock_process, mock_anthropic):
    # Mock routing
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="sales")]
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic.return_value = mock_client

    mock_process.return_value = {
        "type": "message",
        "message": "Sales agent response",
        "findings": {"leads": 5}
    }

    orchestrator = AgentOrchestrator()
    response = await orchestrator.run(user_id="test_user", query="scrape ouedkniss")

    assert response["message"] == "Sales agent response"
    assert "agent_trace" in response
    assert len(response["agent_trace"]) > 0
    assert "sales" in response["agent_trace"][1]
