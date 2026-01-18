# 🇩🇿 AI Workflow Platform - 2026 Edition

## 📊 Platform Overview

The **AI Workflow Platform** is a state-of-the-art, multi-agent automation ecosystem specifically engineered for the Algerian business market. Established in January 2026, it leverages the latest advancements in **Agentic AI**, **Event-Driven Architecture (EDA)**, and **Post-Quantum Cryptography (PQC)** readiness to provide a robust, scalable, and secure foundation for the next decade.

### 🚀 Key Capabilities (2026 Architecture)

- **Multi-Agent Orchestration (MAS)**: Coordinated reasoning between specialized agents (Sales, Logistics, Finance).
- **Event-Driven Foundation**: Asynchronous execution using high-performance event buses for massive scale.
- **Privacy-First LLM Gateway**: Seamless switching between Cloud (Anthropic) and Local inference sidecars to protect sensitive data.
- **Zero-Trust Security**: Granular scope-based authorization and hybrid future-proof encryption.
- **Automated Governance**: Real-time generation of Workflow SBOMs (Software Bill of Materials) for complete auditability.

---

## 📚 Documentation Index

To explore the platform in depth, please refer to the following structured guides:

| Guide | Description |
|-------|-------------|
| [**Architecture Overview**](ARCHITECTURE.md) | High-level system design and Mermaid diagrams. |
| [**Agent Development Guide**](docs/AGENT_GUIDE.md) | How to build and coordinate specialized AI agents. |
| [**API & Security Spec**](docs/API_AND_SECURITY.md) | Scopes, authentication, and hybrid crypto details. |
| [**Infrastructure & Scale**](docs/INFRASTRUCTURE.md) | Docker orchestration, Event Workers, and LLM sidecars. |
| [**Production Deployment**](docs/PRODUCTION_DEPLOYMENT.md) | Guide for deploying to production (SSL, monitoring, backups). |
| [**Integration Guide**](docs/INTEGRATION_GUIDE.md) | Guide for integrating new templates and tests. |
| [**Upgrade Summary**](docs/UPGRADE_SUMMARY.md) | Summary of latest platform upgrades and features. |
| [**Agentic Contribution**](AGENTS.md) | Rules and context for AI agents working on this repo. |

---

## 🛠 Quick Start (Development)

### Prerequisites
- Docker 24+ & Docker Compose 2.20+
- Python 3.11+
- Node.js 18+
- NVIDIA GPU (Optional, for local LLM sidecar)

### Launch the Stack
```bash
# Configure your secrets
cp .env.example .env

# Start all services (Backend, Frontend, n8n, Redis, Postgres, LLM Sidecar)
cd infrastructure
docker-compose up -d
```

### Access Points
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/docs`
- **n8n Instance**: `http://localhost:5678`
- **Monitoring (Grafana)**: `http://localhost:3001`

---

**Built with ❤️ for Algerian businesses 🇩🇿**
