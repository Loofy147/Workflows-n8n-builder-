# API & Security Specification

## 🔐 Zero-Trust Security Foundation

The platform implements Zero-Trust principles through granular OAuth2 scopes and hybrid cryptography.

### Authorization Scopes
Every JWT token carries a set of `scopes` that define exactly what the bearer can do.

| Scope | Description |
|-------|-------------|
| `agent:chat` | Permission to interact with the AI Orchestrator. |
| `workflow:read` | View status and logs of existing workflows. |
| `workflow:write` | Create or update n8n workflow configurations. |
| `admin:all` | Full administrative access to the platform. |

### Hybrid Post-Quantum Cryptography (PQC)
To survive the "Quantum Decryption Era" predicted for the late 2020s, the platform uses a **Hybrid Cryptographic Layer** (`backend/app/utils/crypto_utils.py`):
- **Classical Layer**: AES-256-GCM for immediate high-speed data protection.
- **Future-Proof Layer**: Structural placeholders for KEM (Key Encapsulation Mechanisms) such as CRYSTALS-Kyber. This ensures that the data architecture is ready for PQC migration without database schema changes.

---

## 📡 Event Bus Interface

The platform uses a Redis-based Event Bus (`backend/app/services/event_bus.py`) to decouple agentic reasoning from long-running execution tasks.

### Core Event Types

1. **`workflow_created`**
   - **Payload**: `{ workflow_id, user_id, template_id, n8n_id }`
   - **Consumer**: Event Worker (Logs to audit, sends welcome notifications).

2. **`workflow_trigger_requested`**
   - **Payload**: `{ workflow_id, data }`
   - **Consumer**: n8n Client (Async execution handling).

---

## 🛠 API Endpoints (Highlights)

- **`POST /api/auth/register`**: Register a new user.
- **`POST /api/auth/login`**: Obtain a JWT token with default scopes.
- **`POST /api/chat/`**: Protected endpoint for agent interaction (Requires `agent:chat`).
- **`GET /api/workflows/templates`**: List available business templates (Requires `workflow:read`).
- **`POST /api/workflows/activate`**: Activate a specific template (Requires `workflow:write`).
