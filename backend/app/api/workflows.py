from fastapi import APIRouter, Depends, HTTPException, Security
from app.services.template_matcher import TemplateMatcher
from app.api.deps import get_current_user
from app.models.user import User
from app.db.session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter()

@router.get("/")
async def get_user_workflows(
    current_user: User = Security(get_current_user, scopes=["workflow:read"]),
    db: Session = Depends(get_db)
):
    from app.models.workflow import UserWorkflow
    workflows = db.query(UserWorkflow).filter(UserWorkflow.user_id == current_user.id).all()
    return workflows

@router.get("/templates")
async def get_templates(
    current_user: User = Security(get_current_user, scopes=["workflow:read"]),
    db: Session = Depends(get_db)
):
    matcher = TemplateMatcher(db=db)
    return matcher.get_all_templates()

@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: User = Security(get_current_user, scopes=["workflow:read"])
):
    # Implementation here
    return {"id": workflow_id}

class WorkflowActivationRequest(BaseModel):
    template_id: str
    inputs: Dict[str, Any]

@router.post("/activate")
async def activate_workflow(
    request: WorkflowActivationRequest,
    current_user: User = Security(get_current_user, scopes=["workflow:write"]),
    db: Session = Depends(get_db)
):
    from app.services.workflow_builder import WorkflowBuilder
    from app.services.template_matcher import TemplateMatcher

    matcher = TemplateMatcher(db=db)
    template = matcher.get_template(request.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    builder = WorkflowBuilder()
    try:
        workflow = await builder.build_from_template(
            template=template,
            user_id=current_user.id,
            inputs=request.inputs,
            db=db
        )
        return {
            "id": workflow.id,
            "name": workflow.name,
            "webhook_url": workflow.webhook_url,
            "status": workflow.status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
