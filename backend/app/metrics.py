from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
WORKFLOW_EXECUTIONS = Counter('workflow_executions_total', 'Total workflow executions', ['status'])
AI_TOKEN_USAGE = Counter('ai_tokens_used_total', 'Total AI tokens consumed', ['model'])
