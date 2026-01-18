from fastapi import APIRouter, Depends, Security
from app.api.deps import get_current_user
from app.models.user import User
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/")
async def get_user_executions(
    current_user: User = Security(get_current_user, scopes=["workflow:read"]),
    db: Session = Depends(get_db)
):
    from app.models.execution import WorkflowExecution
    executions = db.query(WorkflowExecution).filter(WorkflowExecution.user_id == current_user.id).all()
    return executions
