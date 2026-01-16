# Architecture: AI Workflow Platform

## Overview
The AI Workflow Platform is designed to help Algerian businesses automate their operations using AI-driven workflows. It leverages FastAPI for a high-performance backend, React for a modern frontend, and n8n as a powerful workflow execution engine.

## Components

### 1. Backend (FastAPI)
- **AI Agent**: Interprets user requests in Darja, French, or English.
- **Workflow Builder**: Generates n8n workflow JSON from templates.
- **API Layer**: Provides RESTful endpoints for chat, workflows, and monitoring.
- **Cost Estimator**: Tracks and estimates business costs in DZD.

### 2. Workflow Engine (n8n)
- Executes the actual automation logic.
- Managed by the backend via its API.

### 3. Frontend (React)
- **Chat Interface**: Natural language interaction with the AI Agent.
- **Dashboard**: Monitor workflow executions and costs.

### 4. Infrastructure
- **Docker**: Containerized deployment.
- **PostgreSQL**: Primary database.
- **Redis**: Caching and task queueing.

## Data Flow
1. User describes a need in the Chat Interface.
2. AI Agent processes the request, matches it to a template, and asks for parameters.
3. User provides parameters.
4. Workflow Builder creates the workflow in n8n.
5. n8n executes the workflow and reports back.
6. Costs are tracked and displayed to the user.
