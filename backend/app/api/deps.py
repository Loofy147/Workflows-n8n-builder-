from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from fastapi.security import SecurityScopes
from app.db.session import get_db
from app.models.user import User
from app.config import settings
from app.utils.auth_utils import ALGORITHM

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_VERSION}/auth/login",
    scopes={
        "agent:chat": "Chat with the AI agent",
        "workflow:read": "Read workflow data",
        "workflow:write": "Create or modify workflows",
        "admin:all": "Full administrative access"
    }
)

def get_current_user(
    security_scopes: SecurityScopes,
    db: Session = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": authenticate_value},
        )

    # Scope validation
    for scope in security_scopes.scopes:
        if scope not in token_scopes and "admin:all" not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
