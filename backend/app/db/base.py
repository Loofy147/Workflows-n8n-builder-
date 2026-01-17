from app.db.session import Base
# Import all models here to ensure they are registered with Base.metadata
from app.models.user import User
from app.models.workflow import WorkflowTemplate, UserWorkflow, ChatConversation
from app.models.execution import WorkflowExecution
