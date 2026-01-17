from fastapi import APIRouter, Depends
from app.services.template_matcher import TemplateMatcher
from app.db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/templates")
async def get_templates():
    matcher = TemplateMatcher()
    return matcher.get_all_templates()

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    # Implementation here
    return {"id": workflow_id}
