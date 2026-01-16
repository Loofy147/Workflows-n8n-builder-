# 🇩🇿 AI Workflow Platform - Production Deployment Guide

## 📊 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER LAYER                               │
│  Web App (React) ←→ Mobile App ←→ API Clients              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS (Nginx)
┌────────────────────▼────────────────────────────────────────┐
│                BACKEND LAYER (FastAPI)                      │
│  • AI Agent (Claude Sonnet 4)                              │
│  • Workflow Builder                                         │
│  • Authentication & Authorization                           │
│  • Rate Limiting & Cost Tracking                           │
└──────┬──────────┬──────────┬──────────────────────────────┘
       │          │          │
   ┌───▼───┐  ┌──▼──┐   ┌───▼─────────────────────────────┐
   │Postgres│ │Redis│   │  n8n Workflow Engine            │
   │        │ │     │   │  • Hidden from users            │
   │• Users │ │• Q  │   │  • Executes workflows           │
   │• Flows │ │• Cache  │  • Manages credentials          │
   │• Execs │ │     │   │  • Webhooks                     │
   └────────┘ └─────┘   └─────────────────────────────────┘
```

## 🚀 Quick Start (Development)

### Prerequisites

- Docker 24+ & Docker Compose 2.20+
- Python 3.11+
- Node.js 18+
- 4GB RAM minimum
- Anthropic API key

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/ai-workflow-platform.git
cd ai-workflow-platform
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Update with your API keys and passwords
```

**Critical variables to set:**
- `ANTHROPIC_API_KEY` - Get from anthropic.com
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `JWT_SECRET` - Generate with: `openssl rand -hex 32`
- `N8N_ENCRYPTION_KEY` - Generate with: `openssl rand -hex 32`
- All passwords (`DB_PASSWORD`, `REDIS_PASSWORD`, `N8N_PASSWORD`)

### 3. Launch Stack

```bash
cd infrastructure
docker-compose up -d
```

### 4. Verify Services

```bash
# Check all services are healthy
docker-compose ps

# View logs
docker-compose logs -f backend

# Access services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - n8n (admin only): http://localhost:5678
# - Grafana: http://localhost:3001
```

### 5. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Load workflow templates
docker-compose exec backend python -m app.scripts.load_templates

# Create admin user
docker-compose exec backend python -m app.scripts.create_admin \
  --email admin@example.com \
  --password YourSecurePassword
```

## 🏭 Production Deployment

### Infrastructure Requirements

#### Minimum Specs
- **App Server**: 4 vCPU, 8GB RAM, 50GB SSD
- **Database**: 2 vCPU, 4GB RAM, 100GB SSD
- **Redis**: 1 vCPU, 2GB RAM, 20GB SSD
- **Bandwidth**: 1TB/month
- **Estimated cost**: $50-80/month (VPS) or $150-200/month (cloud)

#### Recommended Specs (for 1000+ users)
- **App Cluster**: 3x (8 vCPU, 16GB RAM, 100GB SSD)
- **Database**: RDS/Managed PostgreSQL (4 vCPU, 16GB RAM, 500GB)
- **Redis**: ElastiCache/Managed Redis (2 vCPU, 4GB RAM)
- **Load Balancer**: Application Load Balancer
- **CDN**: CloudFlare/Cloudfront
- **Estimated cost**: $500-800/month

### 1. Server Setup (Ubuntu 22.04 LTS)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deploy user
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy

# Configure firewall
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d api.yourdomain.com \
  -d workflows.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos --non-interactive

# Auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

### 3. Domain Configuration

**DNS Records (CloudFlare):**

```
Type    Name        Value               Proxy
A       @           YOUR_SERVER_IP      Yes
A       api         YOUR_SERVER_IP      Yes
A       workflows   YOUR_SERVER_IP      No  ← Important: n8n webhooks
A       n8n         YOUR_SERVER_IP      Yes
CNAME   www         yourdomain.com      Yes
```

### 4. Production Environment

```bash
# Clone on server
cd /opt
sudo git clone https://github.com/yourorg/ai-workflow-platform.git
sudo chown -R deploy:deploy ai-workflow-platform
cd ai-workflow-platform

# Configure production environment
sudo -u deploy cp .env.example .env
sudo -u deploy nano .env
```

**Production .env changes:**
```bash
ENVIRONMENT=production
DEBUG=false

# Update all URLs with your domain
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com
N8N_WEBHOOK_URL=https://workflows.yourdomain.com

# Strong passwords (generate with: openssl rand -base64 32)
DB_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
N8N_PASSWORD=<strong-password>

# Enable monitoring
SENTRY_DSN=<your-sentry-dsn>

# Production security
FORCE_HTTPS=true
CORS_ORIGINS=["https://yourdomain.com"]
```

### 5. Launch Production Stack

```bash
cd infrastructure

# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Verify all services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Database Setup

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Load templates
docker-compose exec backend python -m app.scripts.load_templates

# Create admin
docker-compose exec backend python -m app.scripts.create_admin \
  --email admin@yourdomain.com \
  --password $(openssl rand -base64 16)
```

### 7. Configure n8n API Key

```bash
# Access n8n UI
open https://n8n.yourdomain.com

# Login with N8N_USER and N8N_PASSWORD
# Go to: Settings → API → Create API Key
# Copy the key and update .env:
N8N_API_KEY=n8n_api_xxxxxxxxxxxxx

# Restart backend to apply
docker-compose restart backend
```

## 📦 Workflow Templates

Templates are stored in `templates/` directory as JSON files.

### Template Structure

```json
{
  "id": "template_id",
  "name": "Template Name",
  "category": "lead_generation",
  "description": "What this workflow does",
  "keywords": ["keyword1", "keyword2"],
  "required_inputs": [
    {
      "name": "category",
      "type": "select",
      "label": "Category",
      "options": ["Option1", "Option2"],
      "validation": "required"
    }
  ],
  "optional_inputs": [],
  "n8n_json": {
    "name": "Workflow_{{user_id}}",
    "nodes": [...]
  },
  "estimated_cost_dzd": 8.0,
  "avg_execution_time_seconds": 45
}
```

### Loading Templates

```bash
# Load all templates
docker-compose exec backend python -m app.scripts.load_templates

# Load specific template
docker-compose exec backend python -m app.scripts.load_templates \
  --file templates/ouedkniss_lead_gen.json

# Validate template
docker-compose exec backend python -m app.scripts.validate_template \
  templates/new_template.json
```

## 🔒 Security Hardening

### 1. Application Security

```bash
# Enable rate limiting
RATE_LIMIT_PER_MINUTE=60

# Enforce HTTPS
FORCE_HTTPS=true

# Strong password policy
MIN_PASSWORD_LENGTH=12
REQUIRE_SPECIAL_CHARS=true

# JWT expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Database Security

```sql
-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE ai_platform TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Enable row-level security
ALTER TABLE user_workflows ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_workflow_access ON user_workflows
  FOR ALL TO app_user
  USING (user_id = current_setting('app.current_user_id'));
```

### 3. Network Security

```nginx
# In nginx.conf
# Restrict n8n admin access
location /n8n/ {
    allow 10.0.0.0/8;      # Internal network
    allow YOUR.VPN.IP.HERE; # Your VPN
    deny all;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

### 4. Secrets Management

```bash
# Use Docker secrets in production
echo "your-secret" | docker secret create db_password -
echo "your-secret" | docker secret create anthropic_key -

# Update docker-compose.prod.yml to use secrets
```

## 📊 Monitoring & Alerting

### Prometheus Metrics

Access: `http://your-server:9090`

**Key Metrics:**
- `http_requests_total` - Total API requests
- `http_request_duration_seconds` - API response time
- `workflow_executions_total` - Workflow runs
- `ai_tokens_used_total` - AI API usage
- `user_credits_balance` - User balances

### Grafana Dashboards

Access: `http://your-server:3001`

**Pre-built dashboards:**
1. **System Overview**: CPU, RAM, disk, network
2. **API Performance**: Request rate, latency, errors
3. **Workflow Analytics**: Execution rate, success rate, costs
4. **User Metrics**: Signups, active users, credit usage
5. **Cost Tracking**: AI costs, execution costs, revenue

### Alert Setup

```yaml
# prometheus/alerts.yml
groups:
  - name: platform_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: LowCredits
        expr: user_credits_balance < 10
        annotations:
          summary: "User low on credits"
```

### Log Management

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f n8n

# Export logs to file
docker-compose logs backend > logs/backend.log

# Log rotation
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 💰 Cost Optimization

### 1. AI Token Management

```python
# Use cheaper models for simple tasks
SIMPLE_TASKS_MODEL = "claude-haiku-3"  # $0.25/1M tokens
COMPLEX_TASKS_MODEL = "claude-sonnet-4"  # $3/1M tokens

# Cache common responses
ENABLE_RESPONSE_CACHE = true
CACHE_TTL_SECONDS = 3600

# Batch API calls
BATCH_SIZE = 10
```

### 2. Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_executions_user_created ON workflow_executions(user_id, created_at);
CREATE INDEX idx_workflows_template ON user_workflows(template_id);

-- Archive old data
DELETE FROM workflow_executions WHERE created_at < NOW() - INTERVAL '90 days';

-- Vacuum database
VACUUM ANALYZE;
```

### 3. Caching Strategy

```python
# Redis cache configuration
CACHE_USER_CONTEXT = 300  # 5 minutes
CACHE_TEMPLATES = 3600    # 1 hour
CACHE_EXECUTION_STATUS = 10  # 10 seconds
```

## 🔄 Backup & Disaster Recovery

### Automated Backups

```bash
#!/bin/bash
# /opt/ai-platform/scripts/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/$DATE"

# Database backup
docker-compose exec -T postgres pg_dump -U platform_user ai_platform \
  > "$BACKUP_DIR/database.sql"

# Redis backup
docker-compose exec -T redis redis-cli --rdb /data/dump.rdb
docker cp platform_redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

# n8n workflows
docker-compose exec -T n8n tar czf - /home/node/.n8n \
  > "$BACKUP_DIR/n8n.tar.gz"

# Upload to S3
aws s3 sync "$BACKUP_DIR" "s3://ai-platform-backups/$DATE/"

# Cleanup old backups (keep 30 days)
find /backups -type d -mtime +30 -exec rm -rf {} \;
```

```bash
# Schedule backup
sudo crontab -e
# Add: 0 2 * * * /opt/ai-platform/scripts/backup.sh
```

### Disaster Recovery

```bash
# Restore from backup
DATE=20260115_020000

# Restore database
docker-compose exec -T postgres psql -U platform_user ai_platform \
  < "/backups/$DATE/database.sql"

# Restore Redis
docker cp "/backups/$DATE/redis.rdb" platform_redis:/data/dump.rdb
docker-compose restart redis

# Restore n8n
docker cp "/backups/$DATE/n8n.tar.gz" platform_n8n:/tmp/
docker-compose exec n8n tar xzf /tmp/n8n.tar.gz -C /
docker-compose restart n8n
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Test specific module
docker-compose exec backend pytest tests/test_ai_agent.py -v
```

### Integration Tests

```bash
# Test AI agent end-to-end
docker-compose exec backend pytest tests/integration/test_workflow_creation.py

# Load testing
pip install locust
locust -f tests/load/locustfile.py --host https://api.yourdomain.com
```

## 📈 Scaling Guide

### Horizontal Scaling

```bash
# Scale backend workers
docker-compose up -d --scale backend=4

# Add load balancer in docker-compose.yml
nginx:
  # ... existing config
  depends_on:
    - backend-1
    - backend-2
    - backend-3
```

### Database Scaling

```sql
-- Enable read replicas
-- Setup on managed DB service (RDS, Cloud SQL, etc.)

-- Connection pooling
POSTGRES_MAX_CONNECTIONS=100
POSTGRES_POOL_SIZE=20
```

### Redis Scaling

```bash
# Redis Cluster mode
redis-cli --cluster create \
  redis1:6379 redis2:6379 redis3:6379 \
  --cluster-replicas 1
```

## 🛠️ Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check disk space
- Review failed workflows

**Weekly:**
- Analyze slow queries
- Review AI token costs
- Check backup integrity

**Monthly:**
- Update dependencies
- Security patches
- Performance tuning
- Database optimization

### Update Procedure

```bash
# Pull latest code
cd /opt/ai-platform
git pull origin main

# Backup current state
./scripts/backup.sh

# Update dependencies
docker-compose -f docker-compose.prod.yml build --no-cache

# Run migrations
docker-compose exec backend alembic upgrade head

# Restart services (zero-downtime)
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend

# Verify
docker-compose ps
curl https://api.yourdomain.com/health
```

## 🆘 Troubleshooting

### Backend Issues

```bash
# Check backend logs
docker-compose logs -f backend

# Restart backend
docker-compose restart backend

# Enter container
docker-compose exec backend bash

# Check database connection
docker-compose exec backend python -c "from app.db.session import engine; print(engine.pool.status())"
```

### n8n Issues

```bash
# Check n8n logs
docker-compose logs -f n8n

# Verify n8n health
curl http://localhost:5678/healthz

# Restart n8n
docker-compose restart n8n

# Check webhook connectivity
curl -X POST https://workflows.yourdomain.com/test-webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Database Issues

```bash
# Check connections
docker-compose exec postgres psql -U platform_user -d ai_platform \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
docker-compose exec postgres psql -U platform_user -d ai_platform \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# Vacuum database
docker-compose exec postgres vacuumdb -U platform_user -d ai_platform --analyze
```

## 📞 Support

- **Documentation**: https://docs.yourdomain.com
- **Issues**: https://github.com/yourorg/ai-workflow-platform/issues
- **Discord**: https://discord.gg/yourserver
- **Email**: support@yourdomain.com

---

**Built with ❤️ for Algerian businesses 🇩🇿**
