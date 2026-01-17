from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.ai_agent import AIWorkflowAgent
from app.api.deps import get_current_user
from app.models.user import User
from app.db.session import get_db
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@router.post("/")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    agent = AIWorkflowAgent()
    response = await agent.process_message(
        user_id=current_user.id,
        message=request.message,
        conversation_id=request.conversation_id,
        db=db
    )
    return response
