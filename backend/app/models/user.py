from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean
from app.db.session import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tier = Column(String, default="free")
    credits_dzd = Column(Float, default=0.0)
    location = Column(String, default="Algeria")
    language_preference = Column(String, default="fr")
    created_at = Column(DateTime, default=datetime.utcnow)
