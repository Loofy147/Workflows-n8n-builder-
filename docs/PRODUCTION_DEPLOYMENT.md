# 🚀 Production Deployment & Upgrade Guide

**TL;DR:** Follow this 6-step checklist to deploy the AI Workflow Platform to production on a VPS/cloud with SSL, monitoring, and backups enabled.

---

## Prerequisites

Before deployment, ensure you have:

1. **Server**: Ubuntu 24.04 LTS VPS (minimum 4GB RAM, 2 CPU cores)
2. **Domain**: Registered domain pointing to your server IP
3. **API Keys**: Anthropic, n8n, social media APIs (see `.env.example`)
4. **SSL Certificate**: Let's Encrypt (automated via Certbot)

---

## Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## Step 2: Clone & Configure

```bash
# Clone repository
git clone https://github.com/your-org/ai-workflow-platform.git
cd ai-workflow-platform

# Create production environment file
cp .env.example .env

# CRITICAL: Edit .env with production values
nano .env
```

### Required Environment Variables

**Database & Redis:**
```bash
DB_PASSWORD=<STRONG_RANDOM_PASSWORD>
REDIS_PASSWORD=<STRONG_RANDOM_PASSWORD>
N8N_DB_PASSWORD=<STRONG_RANDOM_PASSWORD>
```

**AI API Keys:**
```bash
ANTHROPIC_API_KEY=sk-ant-XXXXX  # Get from console.anthropic.com
OPENAI_API_KEY=sk-XXXXX          # Fallback (optional)
```

**n8n Configuration:**
```bash
N8N_USER=admin
N8N_PASSWORD=<STRONG_PASSWORD>
N8N_API_KEY=<GENERATE_IN_N8N_AFTER_FIRST_START>
N8N_ENCRYPTION_KEY=<32_CHAR_RANDOM_STRING>

# Update domains
N8N_HOST=n8n.yourdomain.com
N8N_WEBHOOK_URL=https://workflows.yourdomain.com
N8N_EDITOR_URL=https://n8n.yourdomain.com
```

**Application URLs:**
```bash
FRONTEND_URL=https://app.yourdomain.com
API_URL=https://api.yourdomain.com
CORS_ORIGINS=["https://app.yourdomain.com"]
```

**Algeria Business APIs:**
```bash
YALIDINE_API_KEY=<YOUR_YALIDINE_TOKEN>
CCP_API_KEY=<YOUR_CCP_KEY>
BARIDIMOB_API_KEY=<YOUR_BARIDIMOB_KEY>

WHATSAPP_ACCESS_TOKEN=<FACEBOOK_GRAPH_TOKEN>
WHATSAPP_PHONE_NUMBER_ID=<YOUR_WA_PHONE_ID>
INSTAGRAM_ACCESS_TOKEN=<IG_GRAPH_TOKEN>
```

**Security:**
```bash
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
FORCE_HTTPS=true
```

---

## Step 3: SSL Certificate Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificates for all domains
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com -d n8n.yourdomain.com -d app.yourdomain.com -d grafana.yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/yourdomain.com/
```

Update `infrastructure/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl http2;
    server_name n8n.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://n8n:5678;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com api.yourdomain.com n8n.yourdomain.com app.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Step 4: Deploy Stack

```bash
cd infrastructure

# Pull images
docker-compose pull

# Start services
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Expected output:
# postgres      - Up (healthy)
# redis         - Up (healthy)
# n8n           - Up (healthy)
# backend       - Up (healthy)
# event_worker  - Up
# frontend      - Up (healthy)
# nginx         - Up (healthy)
# prometheus    - Up
# grafana       - Up
```

---

## Step 5: Post-Deployment Configuration

### 5.1 Initialize Database

```bash
# Access backend container
docker exec -it ai_platform_backend bash

# Run migrations
alembic upgrade head

# Create initial admin user (optional)
python -m app.scripts.create_admin_user
```

### 5.2 Configure n8n

1. Access n8n: `https://n8n.yourdomain.com`
2. Complete initial setup with credentials from `.env`
3. Generate API key:
   - Settings → API → Create new API key
   - Copy key to `.env` as `N8N_API_KEY`
   - Restart backend: `docker-compose restart backend`

### 5.3 Setup Monitoring

Access Grafana: `https://grafana.yourdomain.com`

Default credentials: `admin` / `<GRAFANA_PASSWORD from .env>`

**Import dashboards:**
1. Go to Dashboards → Import
2. Upload JSON from `infrastructure/grafana/dashboards/`
3. Configure Prometheus data source (already provisioned)

**Key metrics to monitor:**
- AI token usage per user
- Workflow execution success rate
- API response times
- Database connection pool
- Redis memory usage

---

## Step 6: Backup Configuration

### Automated Daily Backups

```bash
# Create backup script
sudo nano /usr/local/bin/backup-platform.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ai-platform"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec ai_platform_postgres pg_dump -U platform_user ai_platform | gzip > $BACKUP_DIR/db_$DATE.sql.gz
docker exec ai_platform_postgres pg_dump -U n8n_user n8n | gzip > $BACKUP_DIR/n8n_db_$DATE.sql.gz

# Backup n8n workflows
docker exec ai_platform_n8n tar czf - /home/node/.n8n > $BACKUP_DIR/n8n_data_$DATE.tar.gz

# Backup Redis (if AOF enabled)
docker exec ai_platform_redis redis-cli --rdb /data/dump.rdb save
docker cp ai_platform_redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Delete backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
sudo chmod +x /usr/local/bin/backup-platform.sh

# Schedule daily backups at 2 AM
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-platform.sh >> /var/log/platform-backup.log 2>&1
```

---

## Monitoring & Alerts

### Set up Sentry (Error Tracking)

1. Create free account: https://sentry.io
2. Create new project → Python/FastAPI
3. Copy DSN to `.env`:
   ```bash
   SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
   ```
4. Restart backend: `docker-compose restart backend`

### Prometheus Alerts

Edit `infrastructure/prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alerts.yml'
```

Create `infrastructure/alerts.yml`:

```yaml
groups:
  - name: platform_alerts
    rules:
      - alert: HighAITokenUsage
        expr: rate(ai_tokens_used_total[5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High AI token consumption detected"

      - alert: WorkflowExecutionFailures
        expr: rate(workflow_executions_total{status="failed"}[10m]) > 5
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Multiple workflow failures detected"
```

---

## Scaling for Production

### Horizontal Scaling

**Backend API (Stateless):**
```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

**Event Workers:**
```yaml
event_worker:
  deploy:
    replicas: 2
```

### Database Optimization

```sql
-- Add indexes for frequent queries
CREATE INDEX idx_workflows_user_status ON user_workflows(user_id, status);
CREATE INDEX idx_executions_workflow ON workflow_executions(workflow_id, created_at DESC);
CREATE INDEX idx_conversations_user ON chat_conversations(user_id, created_at DESC);

-- Enable query logging (monitor slow queries)
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1s
```

### Redis Optimization

```bash
# Update docker-compose.yml
redis:
  command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban (Brute Force Protection)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Docker Security

```bash
# Run containers as non-root
# Already configured in Dockerfiles with USER directive

# Scan images for vulnerabilities
docker scan ai_platform_backend
```

### 4. Rate Limiting

Already implemented in FastAPI middleware. Adjust in `backend/app/main.py`:

```python
RATE_LIMIT_PER_MINUTE = 60  # Requests per minute per user
```

---

## Upgrade Procedure

### Zero-Downtime Deployment

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose build

# Rolling update (one service at a time)
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
docker-compose up -d --no-deps --build event_worker

# Verify health
curl https://api.yourdomain.com/health
```

### Database Migrations

```bash
# Always backup before migration
/usr/local/bin/backup-platform.sh

# Run migration
docker exec ai_platform_backend alembic upgrade head

# Rollback if needed
docker exec ai_platform_backend alembic downgrade -1
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend -f

# Common issues:
# - Database connection: Verify DATABASE_URL
# - Redis connection: Verify REDIS_URL
# - Missing API keys: Check .env
```

### n8n Workflows Failing

```bash
# Check n8n logs
docker-compose logs n8n -f

# Verify API connectivity
docker exec ai_platform_backend curl http://n8n:5678/api/v1/workflows

# Regenerate n8n API key if authentication fails
```

### High Memory Usage

```bash
# Check resource consumption
docker stats

# Identify heavy container
# Solution: Increase limits in docker-compose.yml or scale horizontally
```

---

## Cost Optimization (Algeria-Specific)

### 1. Use Local LLM for Privacy-Sensitive Data

Edit `backend/app/services/llm_gateway.py` to route CCP/payment data through local inference:

```python
if contains_sensitive_data(messages):
    return await self._get_local_completion(messages, system, temperature)
```

### 2. Implement Token Caching

```python
# Cache common AI responses
@cache_response(ttl=3600)
async def get_ai_response(prompt):
    ...
```

### 3. Batch API Calls

```python
# Process multiple orders in single Yalidine API call
batch_shipments = chunk_list(orders, 50)
for batch in batch_shipments:
    yalidine_client.create_bulk_shipments(batch)
```

---

## Performance Benchmarks

**Expected Performance (4 CPU / 8GB RAM):**

| Metric | Target | Monitoring |
|--------|--------|------------|
| API Response Time (p95) | < 200ms | Prometheus |
| Workflow Creation | < 3s | Application logs |
| AI Token Processing | 50 req/min | Token counter |
| Database Queries | < 100ms | Slow query log |
| Redis Operations | < 5ms | Redis INFO |

---

## Compliance & Governance

### GDPR/Algeria Data Protection

1. **Data Encryption**: Already implemented (AES-GCM + PQC-ready)
2. **Data Retention**: Configure in `.env`:
   ```bash
   DATA_RETENTION_DAYS=365
   ```
3. **User Data Export**: API endpoint `/api/users/{user_id}/export`
4. **Audit Logging**: All workflows generate SBOM for traceability

### Workflow SBOM Example

Every generated workflow includes a Software Bill of Materials:

```json
{
  "sbom_version": "1.0",
  "workflow_id": "wf_123",
  "components": [
    {"name": "LLM Provider", "model": "claude-sonnet-4"},
    {"name": "n8n Engine", "version": "latest"},
    {"name": "Yalidine Integration", "version": "v1"}
  ],
  "governance": {
    "jurisdiction": "Algeria",
    "data_privacy": "Safe-Processing-2026"
  }
}
```

---

## Next Steps

1. **Load Testing**: Use `locust` or `k6` to simulate 100+ concurrent users
2. **CI/CD Pipeline**: Set up GitHub Actions for automated testing and deployment
3. **Multi-Region**: Deploy Redis Sentinel for high availability
4. **CDN**: Use Cloudflare for frontend asset caching

**Need help?** Check the [troubleshooting guide](docs/TROUBLESHOOTING.md) or open an issue on GitHub.

---

**Deployment completed?** Test the full workflow:
```bash
curl -X POST https://api.yourdomain.com/api/chat/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "I need to automate Ouedkniss leads for real estate in Alger"}'
```
