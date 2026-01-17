from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float
from app.db.session import Base
from datetime import datetime
import uuid

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    description = Column(String)
    keywords = Column(JSON)
    required_inputs = Column(JSON)
    optional_inputs = Column(JSON)
    n8n_json = Column(JSON)
    estimated_cost_dzd = Column(Float)
    avg_execution_time_seconds = Column(Float)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "keywords": self.keywords,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "estimated_cost_dzd": self.estimated_cost_dzd,
            "avg_execution_time_seconds": self.avg_execution_time_seconds
        }

class UserWorkflow(Base):
    __tablename__ = "user_workflows"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    template_id = Column(String, ForeignKey("workflow_templates.id"))
    n8n_workflow_id = Column(String)
    name = Column(String)
    status = Column(String, default="active")
    webhook_url = Column(String)
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    messages = Column(JSON) # List of roles and content
    created_at = Column(DateTime, default=datetime.utcnow)
