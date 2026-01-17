from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_agent import AIWorkflowAgent
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str # In real app, get from auth

@router.post("/")
async def chat(request: ChatRequest):
    agent = AIWorkflowAgent()
    response = await agent.process_message(
        user_id=request.user_id,
        message=request.message,
        conversation_id=request.conversation_id
    )
    return response
