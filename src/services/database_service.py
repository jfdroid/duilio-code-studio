"""
Database Service
================
Service layer for database operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db_session, Base
from core.models import UserPreference, ConversationHistory, SystemMetric
from core.logger import get_logger


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self):
        self.logger = get_logger()
    
    # === User Preferences ===
    
    def get_preference(self, user_id: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        db = get_db_session()
        try:
            pref = db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.key == key
            ).first()
            
            if pref:
                return pref.value
            return default
        except Exception as e:
            self.logger.error(f"Error getting preference: {e}")
            return default
        finally:
            db.close()
    
    def set_preference(self, user_id: str, key: str, value: str) -> bool:
        """
        Set user preference.
        
        Args:
            user_id: User identifier
            key: Preference key
            value: Preference value
            
        Returns:
            True if successful
        """
        db = get_db_session()
        try:
            pref = db.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.key == key
            ).first()
            
            if pref:
                pref.value = value
                pref.updated_at = datetime.now()
            else:
                pref = UserPreference(user_id=user_id, key=key, value=value)
                db.add(pref)
            
            db.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_all_preferences(self, user_id: str) -> Dict[str, str]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of preferences
        """
        db = get_db_session()
        try:
            prefs = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()
            
            return {pref.key: pref.value for pref in prefs}
        except Exception as e:
            self.logger.error(f"Error getting all preferences: {e}")
            return {}
        finally:
            db.close()
    
    # === Conversation History ===
    
    def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        workspace_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save conversation message.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            model: Model used (optional)
            workspace_path: Workspace path (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            True if successful
        """
        db = get_db_session()
        try:
            message = ConversationHistory(
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content,
                model=model,
                workspace_path=workspace_path,
                extra_data=metadata or {}
            )
            db.add(message)
            db.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            user_id: User identifier
            session_id: Optional session identifier
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        db = get_db_session()
        try:
            query = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id
            )
            
            if session_id:
                query = query.filter(ConversationHistory.session_id == session_id)
            
            messages = query.order_by(desc(ConversationHistory.created_at)).limit(limit).all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "model": msg.model,
                    "workspace_path": msg.workspace_path,
                    "metadata": msg.extra_data,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in reversed(messages)  # Reverse to get chronological order
            ]
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
        finally:
            db.close()
    
    def get_sessions(self, user_id: str, limit: int = 20) -> List[str]:
        """
        Get list of session IDs for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions
            
        Returns:
            List of session IDs
        """
        db = get_db_session()
        try:
            sessions = db.query(ConversationHistory.session_id).filter(
                ConversationHistory.user_id == user_id
            ).distinct().order_by(desc(ConversationHistory.created_at)).limit(limit).all()
            
            return [s[0] for s in sessions]
        except Exception as e:
            self.logger.error(f"Error getting sessions: {e}")
            return []
        finally:
            db.close()
    
    # === System Metrics ===
    
    def save_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save system metric.
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            error: Error message if failed
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        db = get_db_session()
        try:
            metric = SystemMetric(
                operation=operation,
                duration_ms=duration_ms,
                success=success,
                error=error,
                extra_data=metadata or {}
            )
            db.add(metric)
            db.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error saving metric: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_metrics(
        self,
        operation: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get system metrics.
        
        Args:
            operation: Optional operation filter
            limit: Maximum number of metrics
            
        Returns:
            List of metrics
        """
        db = get_db_session()
        try:
            query = db.query(SystemMetric)
            
            if operation:
                query = query.filter(SystemMetric.operation == operation)
            
            metrics = query.order_by(desc(SystemMetric.created_at)).limit(limit).all()
            
            return [
                {
                    "operation": m.operation,
                    "duration_ms": m.duration_ms,
                    "success": m.success,
                    "error": m.error,
                    "metadata": m.extra_data,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in metrics
            ]
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return []
        finally:
            db.close()


# Singleton instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create DatabaseService instance."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
