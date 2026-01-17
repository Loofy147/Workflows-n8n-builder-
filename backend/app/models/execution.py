from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from app.db.session import Base
from datetime import datetime

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    workflow_id = Column(String, ForeignKey("user_workflows.id"))
    n8n_execution_id = Column(String)
    status = Column(String)
    cost_dzd = Column(Float)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
