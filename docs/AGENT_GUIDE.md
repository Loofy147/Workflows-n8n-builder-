# AI Agent Orchestration Guide

This guide explains how to work with the **Agent Orchestrator** and implement new specialized agent personas.

## 🤖 The Agent Orchestrator

The `AgentOrchestrator` (`backend/app/services/orchestrator.py`) acts as the "brain" of the platform. It handles:
1. **Initial Intent Classification**: Determining which domain expert should handle the user request.
2. **State Management**: Keeping track of `findings` and `trace` across multi-turn interactions.
3. **Delegation**: Passing the context to the specialized `AIWorkflowAgent` instance.

## 🎭 Implementing Specialized Personas

Personas are defined in `backend/app/services/ai_agent.py`. Each persona is tailored for a specific Algerian business domain.

### Existing Personas
- **Sales**: Lead generation (Ouedkniss), CRM, and social media outreach.
- **Logistics**: Delivery automation (Yalidine) and order fulfillment.
- **Finance**: Payment tracking (Baridimob, CCP) and automated invoicing.

### Adding a New Persona
1. Update `role_personas` dictionary in `AIWorkflowAgent._build_system_prompt`.
2. Update the routing logic in `AgentOrchestrator._route_request` to detect keywords relevant to the new domain.
3. Add domain-specific templates to the `templates/` directory.

## 🛤 Tracing & Auditability

The platform implements **Agentic Tracing**. Every step taken by an agent is appended to the `trace` list in `AgentState`.
- **Purpose**: Debugging complex multi-agent interactions and providing transparency to the user.
- **Implementation**: Managed via the `orchestrator_state` parameter in the `process_message` method.

## 🔌 Tool Integration

Agents can trigger n8n workflows as "tools". When an agent reaches a `workflow_ready` state:
1. It generates a standardized JSON activation form.
2. The UI renders this form for user confirmation.
3. Upon confirmation, the backend activates the n8n workflow.
