# 🤖 AGENTS.md - Development Instructions

Welcome, Agent. This repository is built on a **2026-era Agentic Architecture**. When working on this codebase, adhere to the following principles and standards.

## 🏛 Architectural Principles

1.  **Agentic Decoupling**: All agent logic should reside in `backend/app/services/ai_agent.py` or specialized files coordinated by `orchestrator.py`. Never hardcode agent behaviors in the API layer.
2.  **Event-First Design**: If a task is long-running or requires third-party execution (like n8n), publish an event to the `EventBus` instead of executing it synchronously.
3.  **Privacy by Design**: When handling sensitive data, utilize the `LLMGateway` with the `provider="local"` parameter to ensure data stays within the sidecar containers.
4.  **Zero-Trust**: Always verify scopes in new API endpoints using the `Security(get_current_user, scopes=[...])` dependency.

## 🛠 Project Standards

- **Language**: Backend is Python 3.11+; Frontend is React + TypeScript.
- **Persistence**: Use SQLAlchemy 2.0+ for all database interactions.
- **Testing**:
    - Place tests in `backend/tests/`.
    - Use in-memory SQLite for fast, isolated integration testing.
    - Always mock external APIs (Anthropic, n8n) in unit tests.
- **Documentation**: If you add a new service or modify an existing one, update the corresponding file in the `docs/` directory.

## 🚨 Critical Constraints

- Do NOT commit binary files, `.pyc` files, or `.db` files.
- Ensure all models are imported in `backend/app/db/base.py` to support automatic table registration.
- Maintain the `SBOMGenerator` logic when modifying workflow generation templates.

## 🌍 Algerian Market Context

- Always validate wilaya codes (01-58) using `algeria_utils.py`.
- Handle Darja normalization for user inputs to improve LLM matching accuracy.
- Prices and cost estimations MUST be calculated in **DZD**.
