"""
Database Models
===============
SQLAlchemy models for persistent data.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from core.database import Base


class UserPreference(Base):
    """User preferences model."""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    key = Column(String, nullable=False, index=True)
    value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, key={self.key})>"


class ConversationHistory(Base):
    """Conversation history model."""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model = Column(String)
    workspace_path = Column(String)
    metadata = Column(JSON)  # Additional metadata (tokens, duration, etc.)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ConversationHistory(session_id={self.session_id}, role={self.role})>"


class SystemMetric(Base):
    """System metrics for analytics."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String, nullable=False, index=True)
    duration_ms = Column(Float, nullable=False)
    success = Column(Boolean, default=True)
    error = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SystemMetric(operation={self.operation}, duration_ms={self.duration_ms})>"
