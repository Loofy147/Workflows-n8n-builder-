# Infrastructure & Scale

## 🐳 Docker Orchestration

The platform is designed for high availability and modular scaling using Docker Compose (or Kubernetes in production).

### Core Services
- **Backend (FastAPI)**: Stateless API gateway and agent orchestrator.
- **Event Worker**: Dedicated consumer for background event processing.
- **Frontend (React)**: Containerized static build served via Nginx.
- **n8n**: The core workflow engine, managed via API.
- **Redis**: Shared state for caching, session memory, and the Event Bus.
- **Postgres**: Primary persistent storage for users, workflows, and logs.

## 🧠 Local Inference Sidecars

To ensure data privacy for sensitive Algerian business operations, the platform supports **Local LLM Sidecars**.
- **Container**: `local_inference` (using vLLM or Ollama compatible APIs).
- **Strategy**: The `LLMGateway` (`backend/app/services/llm_gateway.py`) allows routing sensitive messages to the local container instead of external cloud APIs (e.g. Anthropic).
- **Cost Impact**: Reduces token-based cloud costs for high-volume internal tasks.

## 📈 Observability Stack

The infrastructure includes a complete monitoring suite:
- **Prometheus**: Scrapes metrics from the `/metrics` endpoint (token usage, execution count, latency).
- **Grafana**: Visualizes system health and business KPIs.
- **Sentry**: (Optional) For real-time error tracking and alerting.

## 💾 Disaster Recovery
- **Postgres Backups**: Daily snapshots of the `ai_platform` and `n8n` databases.
- **Stateful Volumes**: Persistent data for Redis (AOF) and Postgres to survive container restarts.
