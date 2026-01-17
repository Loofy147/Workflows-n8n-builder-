"""
Agent Orchestrator
Coordinates multi-agent collaboration and state management for complex workflows.
Implements 2026 best practices for Agentic AI.
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from app.services.ai_agent import AIWorkflowAgent

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Represents the current state of a multi-agent conversation"""
    user_id: str
    query: str
    history: List[Dict] = field(default_factory=list)
    findings: Dict[str, Any] = field(default_factory=dict)
    next_agent: Optional[str] = None
    is_complete: bool = False
    trace: List[str] = field(default_factory=list)

class AgentOrchestrator:
    """
    Coordinates specialized agents (Sales, Logistics, Finance) to solve complex user requests.
    Uses a routing-and-delegation pattern.
    """

    def __init__(self):
        self.agents = {
            "sales": AIWorkflowAgent(role="sales"),
            "logistics": AIWorkflowAgent(role="logistics"),
            "finance": AIWorkflowAgent(role="finance"),
            "general": AIWorkflowAgent(role="general")
        }

    async def run(self, user_id: str, query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for multi-agent coordination.
        """
        state = AgentState(user_id=user_id, query=query)
        state.trace.append(f"Orchestrator received query: {query}")

        # 1. Intent Analysis & Routing
        route = await self._route_request(state)
        state.next_agent = route
        state.trace.append(f"Routing to specialized agent: {route}")

        # 2. Agent Execution
        agent = self.agents.get(route, self.agents["general"])
        response = await agent.process_message(
            user_id=user_id,
            message=query,
            conversation_id=conversation_id,
            orchestrator_state=state
        )

        # 3. State Aggregation
        state.findings.update(response.get("findings", {}))
        state.trace.append(f"Agent {route} completed task")

        # Add trace to response for auditability
        response["agent_trace"] = state.trace
        return response

    async def _route_request(self, state: AgentState) -> str:
        """
        Determines which specialized agent should handle the request.
        """
        query_lower = state.query.lower()
        if any(w in query_lower for w in ["ouedkniss", "leads", "sales", "client"]):
            return "sales"
        if any(w in query_lower for w in ["delivery", "yalidine", "ship", "transport"]):
            return "logistics"
        if any(w in query_lower for w in ["payment", "baridimob", "ccp", "invoice"]):
            return "finance"
        return "general"
