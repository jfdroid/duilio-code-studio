"""
Linguistic Analyzer Service
============================
Advanced NLP-based intent detection focusing on verbs and connecting words.
Uses external JSON data files for scalability and maintainability.
Supports caching for performance optimization.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from functools import lru_cache
from core.logger import get_logger


class VerbCategory(Enum):
    """Categories of verbs based on action type."""
    QUERY = "query"
    EXPLANATION = "explanation"
    COMMAND = "command"
    CONFIRMATION = "confirmation"
    NEGATION = "negation"


class ConnectorType(Enum):
    """Types of connecting words."""
    CAUSAL = "causal"
    INTERROGATIVE = "interrogative"
    CONDITIONAL = "conditional"
    CONTRASTIVE = "contrastive"
    ADDITIVE = "additive"
    TEMPORAL = "temporal"
    COMPARATIVE = "comparative"


class LinguisticAnalysis:
    """Result of linguistic analysis."""
    
    def __init__(self):
        self.main_verb: Optional[str] = None
        self.verb_category: Optional[VerbCategory] = None
        self.verbs: List[Tuple[str, VerbCategory, float]] = []  # (verb, category, weight)
        self.connectors: List[Tuple[str, ConnectorType, float]] = []  # (connector, type, weight)
        self.patterns_matched: List[Tuple[str, str, float]] = []  # (pattern_name, pattern_type, weight)
        self.requires_explanation: bool = False
        self.requires_data: bool = False
        self.requires_action: bool = False
        self.intent: Optional[str] = None
        self.confidence: float = 0.0
        self.analysis_metadata: Dict[str, Any] = {}


class LinguisticDataLoader:
    """Loads and manages linguistic data from JSON files."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to data/linguistic relative to project root
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "linguistic"
        
        self.data_dir = data_dir
        self.logger = get_logger()
        self._verbs_data: Optional[Dict] = None
        self._connectors_data: Optional[Dict] = None
        self._patterns_data: Optional[Dict] = None
    
    @lru_cache(maxsize=1)
    def load_verbs(self) -> Dict[str, Any]:
        """Load verbs data from JSON file."""
        if self._verbs_data is None:
            verbs_file = self.data_dir / "verbs.json"
            try:
                with open(verbs_file, 'r', encoding='utf-8') as f:
                    self._verbs_data = json.load(f)
                self.logger.info(f"Loaded verbs data from {verbs_file}")
            except FileNotFoundError:
                self.logger.warning(f"Verbs file not found: {verbs_file}, using empty data")
                self._verbs_data = {}
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing verbs.json: {e}")
                self._verbs_data = {}
        return self._verbs_data
    
    @lru_cache(maxsize=1)
    def load_connectors(self) -> Dict[str, Any]:
        """Load connectors data from JSON file."""
        if self._connectors_data is None:
            connectors_file = self.data_dir / "connectors.json"
            try:
                with open(connectors_file, 'r', encoding='utf-8') as f:
                    self._connectors_data = json.load(f)
                self.logger.info(f"Loaded connectors data from {connectors_file}")
            except FileNotFoundError:
                self.logger.warning(f"Connectors file not found: {connectors_file}, using empty data")
                self._connectors_data = {}
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing connectors.json: {e}")
                self._connectors_data = {}
        return self._connectors_data
    
    @lru_cache(maxsize=1)
    def load_patterns(self) -> Dict[str, Any]:
        """Load patterns data from JSON file."""
        if self._patterns_data is None:
            patterns_file = self.data_dir / "patterns.json"
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self._patterns_data = json.load(f)
                self.logger.info(f"Loaded patterns data from {patterns_file}")
            except FileNotFoundError:
                self.logger.warning(f"Patterns file not found: {patterns_file}, using empty data")
                self._patterns_data = {}
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing patterns.json: {e}")
                self._patterns_data = {}
        return self._patterns_data
    
    def get_all_verbs(self, category: str, language: str = "portuguese") -> List[str]:
        """Get all verb forms for a category and language."""
        verbs_data = self.load_verbs()
        if category not in verbs_data:
            return []
        
        category_data = verbs_data[category]
        if language not in category_data:
            return []
        
        lang_data = category_data[language]
        all_verbs = []
        
        # Add base forms
        if "base_forms" in lang_data:
            all_verbs.extend(lang_data["base_forms"])
        
        # Add all conjugations
        if "conjugations" in lang_data:
            for base_form, conjugations in lang_data["conjugations"].items():
                all_verbs.extend(conjugations)
        
        # Add patterns for negation
        if "patterns" in lang_data:
            all_verbs.extend(lang_data["patterns"])
        
        return list(set(all_verbs))  # Remove duplicates
    
    def get_connectors(self, connector_type: str, language: str = "portuguese") -> List[str]:
        """Get connectors for a type and language."""
        connectors_data = self.load_connectors()
        if connector_type not in connectors_data:
            return []
        
        type_data = connectors_data[connector_type]
        if language not in type_data:
            return []
        
        return type_data[language]
    
    def get_patterns(self, pattern_type: str, language: str = "portuguese") -> List[Tuple[str, float]]:
        """Get patterns for a type and language, returning (pattern, weight) tuples."""
        patterns_data = self.load_patterns()
        if pattern_type not in patterns_data:
            return []
        
        type_data = patterns_data[pattern_type]
        patterns = []
        
        for pattern_name, pattern_info in type_data.items():
            if language in pattern_info:
                weight = pattern_info.get("weight", 1.0)
                for pattern_text in pattern_info[language]:
                    patterns.append((pattern_text, weight))
        
        return patterns


class LinguisticAnalyzer:
    """
    Advanced linguistic analyzer focusing on verbs and connecting words.
    
    Uses external JSON data files for scalability and maintainability.
    Supports caching and pattern matching for better performance.
    """
    
    def __init__(self, data_loader: Optional[LinguisticDataLoader] = None):
        self.logger = get_logger()
        self.data_loader = data_loader or LinguisticDataLoader()
        
        # Cache for verb mappings (computed once)
        self._verb_cache: Dict[str, List[Tuple[str, VerbCategory, float]]] = {}
        self._connector_cache: Dict[str, List[Tuple[str, ConnectorType, float]]] = {}
    
    def analyze(self, text: str) -> LinguisticAnalysis:
        """
        Perform comprehensive linguistic analysis of user input.
        
        Args:
            text: User's message
            
        Returns:
            LinguisticAnalysis with extracted information
        """
        analysis = LinguisticAnalysis()
        text_lower = text.lower()
        
        # Extract verbs with weights
        verbs_found = self._extract_verbs(text_lower)
        analysis.verbs = verbs_found
        
        if verbs_found:
            # Main verb is the one with highest weight
            analysis.main_verb, analysis.verb_category, _ = max(verbs_found, key=lambda x: x[2])
        
        # Extract connectors with weights
        connectors_found = self._extract_connectors(text_lower)
        analysis.connectors = connectors_found
        
        # Match patterns
        patterns_found = self._match_patterns(text_lower)
        analysis.patterns_matched = patterns_found
        
        # Determine requirements based on analysis
        analysis.requires_explanation = self._requires_explanation(analysis)
        analysis.requires_data = self._requires_data(analysis)
        analysis.requires_action = self._requires_action(analysis)
        
        # Map to intent
        analysis.intent = self._map_to_intent(analysis)
        analysis.confidence = self._calculate_confidence(analysis)
        
        # Store metadata
        analysis.analysis_metadata = {
            "total_verbs": len(verbs_found),
            "total_connectors": len(connectors_found),
            "total_patterns": len(patterns_found),
            "text_length": len(text),
        }
        
        return analysis
    
    def _extract_verbs(self, text: str) -> List[Tuple[str, VerbCategory, float]]:
        """Extract verbs and categorize them with weights."""
        verbs = []
        found_categories = set()
        
        # Category priority (higher priority = checked first)
        category_priority = [
            (VerbCategory.COMMAND, "command"),
            (VerbCategory.QUERY, "query"),
            (VerbCategory.EXPLANATION, "explanation"),
            (VerbCategory.CONFIRMATION, "confirmation"),
            (VerbCategory.NEGATION, "negation"),
        ]
        
        for verb_category, category_key in category_priority:
            if verb_category in found_categories:
                continue
            
            # Get verbs for this category (try both languages)
            for language in ["portuguese", "english"]:
                verb_list = self.data_loader.get_all_verbs(category_key, language)
                
                for verb in verb_list:
                    # Use word boundaries to avoid partial matches
                    pattern = r'\b' + re.escape(verb) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        # Get weight from data
                        verbs_data = self.data_loader.load_verbs()
                        weight = verbs_data.get(category_key, {}).get("weight", 1.0)
                        verbs.append((verb, verb_category, weight))
                        found_categories.add(verb_category)
                        break  # Only one verb per category
                
                if verb_category in found_categories:
                    break
        
        return verbs
    
    def _extract_connectors(self, text: str) -> List[Tuple[str, ConnectorType, float]]:
        """Extract connecting words and categorize them with weights."""
        connectors = []
        found_types = set()
        
        # Map connector type keys to enum
        connector_type_map = {
            "causal": ConnectorType.CAUSAL,
            "interrogative": ConnectorType.INTERROGATIVE,
            "conditional": ConnectorType.CONDITIONAL,
            "contrastive": ConnectorType.CONTRASTIVE,
            "additive": ConnectorType.ADDITIVE,
            "temporal": ConnectorType.TEMPORAL,
            "comparative": ConnectorType.COMPARATIVE,
        }
        
        connectors_data = self.data_loader.load_connectors()
        
        for type_key, connector_type in connector_type_map.items():
            if connector_type in found_types:
                continue
            
            for language in ["portuguese", "english"]:
                connector_list = self.data_loader.get_connectors(type_key, language)
                
                for connector in connector_list:
                    # Use word boundaries
                    pattern = r'\b' + re.escape(connector) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        # Get weight from data
                        weight = connectors_data.get(type_key, {}).get("weight", 1.0)
                        connectors.append((connector, connector_type, weight))
                        found_types.add(connector_type)
                        break
                
                if connector_type in found_types:
                    break
        
        return connectors
    
    def _match_patterns(self, text: str) -> List[Tuple[str, str, float]]:
        """Match intent and context patterns."""
        patterns_matched = []
        
        # Try both languages
        for language in ["portuguese", "english"]:
            # Intent patterns
            intent_patterns = self.data_loader.get_patterns("intent_patterns", language)
            for pattern, weight in intent_patterns:
                if pattern.lower() in text:
                    patterns_matched.append((pattern, "intent", weight))
            
            # Context patterns
            context_patterns = self.data_loader.get_patterns("context_patterns", language)
            for pattern, weight in context_patterns:
                if pattern.lower() in text:
                    patterns_matched.append((pattern, "context", weight))
        
        return patterns_matched
    
    def _requires_explanation(self, analysis: LinguisticAnalysis) -> bool:
        """Determine if user requires explanation."""
        # Check verb category
        if analysis.verb_category == VerbCategory.EXPLANATION:
            return True
        
        # Check for explanation connectors
        explanation_connectors = [
            ConnectorType.CAUSAL,
            ConnectorType.INTERROGATIVE,
        ]
        if any(conn_type in [c[1] for c in analysis.connectors] 
               for conn_type in explanation_connectors):
            return True
        
        # Check for explanation patterns
        explanation_patterns = [p for p in analysis.patterns_matched if p[0] == "explanation_request"]
        if explanation_patterns:
            return True
        
        return False
    
    def _requires_data(self, analysis: LinguisticAnalysis) -> bool:
        """Determine if user requires data/information."""
        if analysis.verb_category == VerbCategory.QUERY:
            return True
        
        # Check for data request patterns
        data_patterns = [p for p in analysis.patterns_matched if "file_listing" in p[0] or "list" in p[0]]
        if data_patterns:
            return True
        
        return False
    
    def _requires_action(self, analysis: LinguisticAnalysis) -> bool:
        """Determine if user requires action/execution."""
        if analysis.verb_category == VerbCategory.COMMAND:
            return True
        
        # Check for action patterns
        action_patterns = [p for p in analysis.patterns_matched 
                          if "creation" in p[0] or "modification" in p[0] or "deletion" in p[0]]
        if action_patterns:
            return True
        
        return False
    
    def _map_to_intent(self, analysis: LinguisticAnalysis) -> Optional[str]:
        """Map linguistic analysis to intent type."""
        if analysis.verb_category == VerbCategory.COMMAND:
            # Check patterns for specific command types
            for pattern_name, pattern_type, _ in analysis.patterns_matched:
                if "creation" in pattern_name:
                    return 'create'
                elif "modification" in pattern_name:
                    return 'update'
                elif "deletion" in pattern_name:
                    return 'delete'
            
            # Fallback to verb analysis
            verb_text = analysis.main_verb or ""
            if any(kw in verb_text for kw in ['criar', 'create', 'fazer', 'make']):
                return 'create'
            elif any(kw in verb_text for kw in ['modificar', 'modify', 'alterar', 'alter']):
                return 'update'
            elif any(kw in verb_text for kw in ['deletar', 'delete', 'remover', 'remove', 'apagar', 'erase']):
                return 'delete'
            return 'command'
        
        elif analysis.verb_category == VerbCategory.QUERY:
            if analysis.requires_explanation:
                return 'explain_query'
            return 'list'
        
        elif analysis.verb_category == VerbCategory.EXPLANATION:
            return 'explain'
        
        elif analysis.verb_category == VerbCategory.CONFIRMATION:
            return 'confirm'
        
        return None
    
    def _calculate_confidence(self, analysis: LinguisticAnalysis) -> float:
        """Calculate confidence score based on analysis quality."""
        confidence = 0.0
        
        # Base confidence from verb detection (weighted)
        if analysis.verbs:
            max_verb_weight = max(v[2] for v in analysis.verbs)
            confidence += 0.3 * max_verb_weight
        
        # Boost from connector detection (weighted)
        if analysis.connectors:
            max_connector_weight = max(c[2] for c in analysis.connectors)
            confidence += 0.2 * max_connector_weight
        
        # Boost from pattern matching (weighted)
        if analysis.patterns_matched:
            max_pattern_weight = max(p[2] for p in analysis.patterns_matched)
            confidence += 0.3 * max_pattern_weight
        
        # Boost from clear category
        if analysis.verb_category:
            confidence += 0.1
        
        # Boost from intent mapping
        if analysis.intent:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def build_structured_context(self, analysis: LinguisticAnalysis) -> str:
        """
        Build structured context string for LLM prompt.
        
        This provides the model with explicit understanding of user intent.
        """
        context_parts = []
        
        if analysis.main_verb:
            context_parts.append(f"VERB_DETECTED: {analysis.main_verb}")
        
        if analysis.verb_category:
            context_parts.append(f"VERB_CATEGORY: {analysis.verb_category.value}")
        
        if analysis.connectors:
            conn_str = ", ".join([f"{c[0]} ({c[1].value}, weight={c[2]:.2f})" for c in analysis.connectors])
            context_parts.append(f"CONNECTORS: {conn_str}")
        
        if analysis.patterns_matched:
            pattern_str = ", ".join([f"{p[0]} ({p[1]}, weight={p[2]:.2f})" for p in analysis.patterns_matched[:3]])
            context_parts.append(f"PATTERNS_MATCHED: {pattern_str}")
        
        if analysis.intent:
            context_parts.append(f"INTENT: {analysis.intent}")
        
        if analysis.requires_explanation:
            context_parts.append("REQUIRES_EXPLANATION: true")
            context_parts.append("INSTRUCTION: Provide detailed reasoning and reference FILE LISTING")
        
        if analysis.requires_data:
            context_parts.append("REQUIRES_DATA: true")
            context_parts.append("INSTRUCTION: Use FILE LISTING to provide exact numbers and names")
        
        if analysis.requires_action:
            context_parts.append("REQUIRES_ACTION: true")
            context_parts.append("INSTRUCTION: Execute the requested action using proper formats")
        
        # Add confidence
        context_parts.append(f"CONFIDENCE: {analysis.confidence:.2f}")
        
        return "\n".join(context_parts)


# Singleton instance
_linguistic_analyzer: Optional[LinguisticAnalyzer] = None


def get_linguistic_analyzer() -> LinguisticAnalyzer:
    """Get or create linguistic analyzer instance."""
    global _linguistic_analyzer
    if _linguistic_analyzer is None:
        _linguistic_analyzer = LinguisticAnalyzer()
    return _linguistic_analyzer
