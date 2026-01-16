CREATE DATABASE n8n;
CREATE USER n8n_user WITH PASSWORD 'your-n8n-db-password-change-me';
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;

-- In production, you would want more restricted permissions
