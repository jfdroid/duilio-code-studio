"""
User Preferences Service
========================
Learns and adapts to user preferences over time.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from core.config import get_settings


@dataclass
class ModelUsage:
    """Track model usage statistics."""
    model: str
    success_count: int = 0
    error_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    last_used: float = 0.0
    categories: Dict[str, int] = field(default_factory=dict)


@dataclass
class UserPreferences:
    """User preferences and learned patterns."""
    preferred_model_code: Optional[str] = None
    preferred_model_general: Optional[str] = None
    preferred_language: str = "auto"  # 'auto', 'en', 'pt-br', etc
    temperature_preference: float = 0.7
    model_usage: Dict[str, ModelUsage] = field(default_factory=dict)
    common_topics: List[str] = field(default_factory=list)
    favorite_languages: List[str] = field(default_factory=list)
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)


class UserPreferencesService:
    """
    Service for learning and managing user preferences.
    
    Features:
    - Track model usage and success rates
    - Learn preferred programming languages
    - Adapt temperature based on feedback
    - Remember common topics and patterns
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.data_file = Path(self.settings.DATA_DIR) / "user_preferences.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self._preferences: Optional[UserPreferences] = None
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        """Load preferences from disk."""
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                
                # Convert model_usage dict
                model_usage = {}
                for model, usage_data in data.get("model_usage", {}).items():
                    model_usage[model] = ModelUsage(
                        model=model,
                        success_count=usage_data.get("success_count", 0),
                        error_count=usage_data.get("error_count", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                        avg_response_time=usage_data.get("avg_response_time", 0.0),
                        last_used=usage_data.get("last_used", 0.0),
                        categories=usage_data.get("categories", {})
                    )
                
                self._preferences = UserPreferences(
                    preferred_model_code=data.get("preferred_model_code"),
                    preferred_model_general=data.get("preferred_model_general"),
                    preferred_language=data.get("preferred_language", "auto"),
                    temperature_preference=data.get("temperature_preference", 0.7),
                    model_usage=model_usage,
                    common_topics=data.get("common_topics", []),
                    favorite_languages=data.get("favorite_languages", []),
                    feedback_history=data.get("feedback_history", [])
                )
            except Exception as e:
                print(f"[DuilioCode] Error loading preferences: {e}")
                self._preferences = UserPreferences()
        else:
            self._preferences = UserPreferences()
    
    def _save_preferences(self) -> None:
        """Save preferences to disk."""
        if not self._preferences:
            return
        
        data = {
            "preferred_model_code": self._preferences.preferred_model_code,
            "preferred_model_general": self._preferences.preferred_model_general,
            "preferred_language": self._preferences.preferred_language,
            "temperature_preference": self._preferences.temperature_preference,
            "model_usage": {
                model: {
                    "success_count": usage.success_count,
                    "error_count": usage.error_count,
                    "total_tokens": usage.total_tokens,
                    "avg_response_time": usage.avg_response_time,
                    "last_used": usage.last_used,
                    "categories": usage.categories
                }
                for model, usage in self._preferences.model_usage.items()
            },
            "common_topics": self._preferences.common_topics[:50],
            "favorite_languages": self._preferences.favorite_languages[:10],
            "feedback_history": self._preferences.feedback_history[-100:]
        }
        
        self.data_file.write_text(json.dumps(data, indent=2))
    
    def get_preferences(self) -> UserPreferences:
        """Get current preferences."""
        return self._preferences
    
    def record_model_usage(
        self,
        model: str,
        success: bool,
        tokens: int = 0,
        response_time: float = 0.0,
        category: Optional[str] = None
    ) -> None:
        """Record a model usage event."""
        if model not in self._preferences.model_usage:
            self._preferences.model_usage[model] = ModelUsage(model=model)
        
        usage = self._preferences.model_usage[model]
        
        if success:
            usage.success_count += 1
        else:
            usage.error_count += 1
        
        usage.total_tokens += tokens
        usage.last_used = time.time()
        
        # Update average response time
        total_uses = usage.success_count + usage.error_count
        usage.avg_response_time = (
            (usage.avg_response_time * (total_uses - 1) + response_time) / total_uses
        )
        
        # Track category usage
        if category:
            usage.categories[category] = usage.categories.get(category, 0) + 1
        
        self._save_preferences()
    
    def record_feedback(
        self,
        positive: bool,
        model: str,
        category: Optional[str] = None,
        notes: Optional[str] = None
    ) -> None:
        """Record user feedback on a response."""
        feedback = {
            "timestamp": time.time(),
            "positive": positive,
            "model": model,
            "category": category,
            "notes": notes
        }
        
        self._preferences.feedback_history.append(feedback)
        
        # Update model preference based on positive feedback
        if positive and category:
            if category in ("code_generation", "code_debug", "code_refactor"):
                # Track code model preference
                if self._preferences.preferred_model_code != model:
                    code_positive = sum(
                        1 for f in self._preferences.feedback_history[-20:]
                        if f.get("model") == model and f.get("positive") and
                        f.get("category", "").startswith("code_")
                    )
                    if code_positive >= 3:
                        self._preferences.preferred_model_code = model
            else:
                # Track general model preference
                if self._preferences.preferred_model_general != model:
                    general_positive = sum(
                        1 for f in self._preferences.feedback_history[-20:]
                        if f.get("model") == model and f.get("positive") and
                        not f.get("category", "").startswith("code_")
                    )
                    if general_positive >= 3:
                        self._preferences.preferred_model_general = model
        
        self._save_preferences()
    
    def record_language_detected(self, language: str) -> None:
        """Record a programming language usage."""
        if language not in self._preferences.favorite_languages:
            self._preferences.favorite_languages.insert(0, language)
            self._preferences.favorite_languages = self._preferences.favorite_languages[:10]
            self._save_preferences()
    
    def record_topic(self, topic: str) -> None:
        """Record a topic discussed."""
        if topic not in self._preferences.common_topics:
            self._preferences.common_topics.insert(0, topic)
            self._preferences.common_topics = self._preferences.common_topics[:50]
            self._save_preferences()
    
    def get_best_model(
        self,
        is_code: bool,
        available_models: List[str]
    ) -> Optional[str]:
        """
        Get the best model based on learned preferences.
        
        Args:
            is_code: Whether the task is code-related
            available_models: List of available models
            
        Returns:
            Recommended model or None if no preference
        """
        # Check explicit preference first
        preferred = (
            self._preferences.preferred_model_code if is_code
            else self._preferences.preferred_model_general
        )
        
        if preferred and preferred in available_models:
            return preferred
        
        # Check model usage statistics
        best_model = None
        best_score = -1
        
        for model in available_models:
            if model in self._preferences.model_usage:
                usage = self._preferences.model_usage[model]
                
                # Calculate score based on success rate and recency
                total = usage.success_count + usage.error_count
                if total > 0:
                    success_rate = usage.success_count / total
                    recency_bonus = min(1.0, (time.time() - usage.last_used) / (86400 * 7))
                    score = success_rate * 0.7 + (1 - recency_bonus) * 0.3
                    
                    if score > best_score:
                        best_score = score
                        best_model = model
        
        return best_model if best_score > 0.6 else None
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a specific preference."""
        if hasattr(self._preferences, key):
            setattr(self._preferences, key, value)
            self._save_preferences()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_requests = sum(
            u.success_count + u.error_count
            for u in self._preferences.model_usage.values()
        )
        
        total_tokens = sum(
            u.total_tokens
            for u in self._preferences.model_usage.values()
        )
        
        positive_feedback = sum(
            1 for f in self._preferences.feedback_history
            if f.get("positive")
        )
        
        negative_feedback = sum(
            1 for f in self._preferences.feedback_history
            if not f.get("positive")
        )
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "preferred_code_model": self._preferences.preferred_model_code,
            "preferred_general_model": self._preferences.preferred_model_general,
            "favorite_languages": self._preferences.favorite_languages[:5],
            "model_usage": {
                model: {
                    "uses": u.success_count + u.error_count,
                    "success_rate": (
                        u.success_count / (u.success_count + u.error_count)
                        if (u.success_count + u.error_count) > 0 else 0
                    )
                }
                for model, u in self._preferences.model_usage.items()
            }
        }


# Singleton instance
_user_preferences_service: Optional[UserPreferencesService] = None


def get_user_preferences_service() -> UserPreferencesService:
    """Get singleton user preferences service instance."""
    global _user_preferences_service
    if _user_preferences_service is None:
        _user_preferences_service = UserPreferencesService()
    return _user_preferences_service
