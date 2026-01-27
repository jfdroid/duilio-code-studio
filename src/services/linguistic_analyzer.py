"""
Linguistic Analyzer Service
============================
Advanced NLP-based intent detection focusing on verbs and connecting words.
Based on best practices: verb extraction, semantic role labeling, and connector analysis.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from core.logger import get_logger


class VerbCategory(Enum):
    """Categories of verbs based on action type."""
    QUERY = "query"  # ver, contar, listar, mostrar
    EXPLANATION = "explanation"  # explicar, por que, como
    COMMAND = "command"  # criar, modificar, deletar
    CONFIRMATION = "confirmation"  # consegue ver, tem acesso, está vendo
    NEGATION = "negation"  # não consegue, não tenho


class ConnectorType(Enum):
    """Types of connecting words."""
    CAUSAL = "causal"  # porque, pois, já que
    INTERROGATIVE = "interrogative"  # por que, como, qual
    CONDITIONAL = "conditional"  # se, quando, caso
    CONTRASTIVE = "contrastive"  # mas, porém, entretanto
    ADDITIVE = "additive"  # e, também, além disso


class LinguisticAnalysis:
    """Result of linguistic analysis."""
    
    def __init__(self):
        self.main_verb: Optional[str] = None
        self.verb_category: Optional[VerbCategory] = None
        self.verbs: List[Tuple[str, VerbCategory]] = []
        self.connectors: List[Tuple[str, ConnectorType]] = []
        self.requires_explanation: bool = False
        self.requires_data: bool = False
        self.requires_action: bool = False
        self.intent: Optional[str] = None
        self.confidence: float = 0.0


class LinguisticAnalyzer:
    """
    Advanced linguistic analyzer focusing on verbs and connecting words.
    
    Principles:
    - Extract main verb to understand action
    - Identify connectors to understand relationships
    - Map verb categories to intent types
    - Provide structured context for LLM
    """
    
    # Verb mappings by category
    VERB_MAPPINGS: Dict[VerbCategory, List[str]] = {
        VerbCategory.QUERY: [
            # Portuguese
            'ver', 'vejo', 'vê', 'vês', 'vemos', 'veem',
            'contar', 'conto', 'conta', 'contamos', 'contam',
            'listar', 'listo', 'lista', 'listamos', 'listam',
            'mostrar', 'mostro', 'mostra', 'mostramos', 'mostram',
            'exibir', 'exibo', 'exibe', 'exibimos', 'exibem',
            'visualizar', 'visualizo', 'visualiza', 'visualizamos', 'visualizam',
            'enumerar', 'enumerar', 'enumera', 'enumeramos', 'enumeram',
            # English
            'see', 'sees', 'saw', 'seeing',
            'count', 'counts', 'counting', 'counted',
            'list', 'lists', 'listing', 'listed',
            'show', 'shows', 'showing', 'showed',
            'display', 'displays', 'displaying', 'displayed',
            'view', 'views', 'viewing', 'viewed',
            'enumerate', 'enumerates', 'enumerating', 'enumerated',
        ],
        VerbCategory.EXPLANATION: [
            # Portuguese
            'explicar', 'explico', 'explica', 'explicamos', 'explicam',
            'justificar', 'justifico', 'justifica', 'justificamos', 'justificam',
            'descrever', 'descrevo', 'descreve', 'descrevemos', 'descrevem',
            'detalhar', 'detalho', 'detalha', 'detalhamos', 'detalham',
            'raciocinar', 'raciocino', 'raciocina', 'raciocinamos', 'raciocinam',
            # English
            'explain', 'explains', 'explaining', 'explained',
            'justify', 'justifies', 'justifying', 'justified',
            'describe', 'describes', 'describing', 'described',
            'detail', 'details', 'detailing', 'detailed',
            'reason', 'reasons', 'reasoning', 'reasoned',
        ],
        VerbCategory.COMMAND: [
            # Portuguese
            'criar', 'crio', 'cria', 'criamos', 'criam',
            'fazer', 'faço', 'faz', 'fazemos', 'fazem',
            'modificar', 'modifico', 'modifica', 'modificamos', 'modificam',
            'alterar', 'altero', 'altera', 'alteramos', 'alteram',
            'deletar', 'deleto', 'deleta', 'deletamos', 'deletam',
            'remover', 'removo', 'remove', 'removemos', 'removem',
            'apagar', 'apago', 'apaga', 'apagamos', 'apagam',
            'excluir', 'excluo', 'exclui', 'excluímos', 'excluem',
            # English
            'create', 'creates', 'creating', 'created',
            'make', 'makes', 'making', 'made',
            'modify', 'modifies', 'modifying', 'modified',
            'alter', 'alters', 'altering', 'altered',
            'delete', 'deletes', 'deleting', 'deleted',
            'remove', 'removes', 'removing', 'removed',
            'erase', 'erases', 'erasing', 'erased',
        ],
        VerbCategory.CONFIRMATION: [
            # Portuguese
            'consegue', 'consigo', 'consegues', 'conseguimos', 'conseguem',
            'pode', 'posso', 'podes', 'podemos', 'podem',
            'tem', 'tenho', 'tens', 'temos', 'têm',
            'está', 'estou', 'estás', 'estamos', 'estão',
            'vendo', 'vendo', 'vendo', 'vendo', 'vendo',
            # English
            'can', 'could', 'able', 'ability',
            'have', 'has', 'having', 'had',
            'is', 'are', 'was', 'were', 'being',
            'seeing', 'see', 'saw',
        ],
        VerbCategory.NEGATION: [
            # Portuguese
            'não consegue', 'não consigo', 'não consegues',
            'não pode', 'não posso', 'não podes',
            'não tem', 'não tenho', 'não tens',
            'não está', 'não estou', 'não estás',
            # English
            "can't", 'cannot', "don't", "doesn't", "didn't",
            "won't", "wouldn't", "isn't", "aren't", "wasn't",
        ],
    }
    
    # Connector mappings
    CONNECTOR_MAPPINGS: Dict[ConnectorType, List[str]] = {
        ConnectorType.CAUSAL: [
            'porque', 'por que', 'pq', 'pois', 'já que', 'visto que',
            'because', 'since', 'as', 'due to', 'owing to',
        ],
        ConnectorType.INTERROGATIVE: [
            'por que', 'pq', 'como', 'qual', 'quais', 'quando', 'onde',
            'why', 'how', 'what', 'which', 'when', 'where',
        ],
        ConnectorType.CONDITIONAL: [
            'se', 'caso', 'quando', 'caso contrário',
            'if', 'when', 'unless', 'otherwise',
        ],
        ConnectorType.CONTRASTIVE: [
            'mas', 'porém', 'entretanto', 'contudo', 'todavia',
            'but', 'however', 'although', 'though', 'yet',
        ],
        ConnectorType.ADDITIVE: [
            'e', 'também', 'além disso', 'ademais', 'ainda',
            'and', 'also', 'furthermore', 'moreover', 'additionally',
        ],
    }
    
    def __init__(self):
        self.logger = get_logger()
    
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
        
        # Extract verbs
        verbs_found = self._extract_verbs(text_lower)
        analysis.verbs = verbs_found
        
        if verbs_found:
            # Main verb is the first one found (usually most important)
            analysis.main_verb, analysis.verb_category = verbs_found[0]
        
        # Extract connectors
        connectors_found = self._extract_connectors(text_lower)
        analysis.connectors = connectors_found
        
        # Determine requirements based on analysis
        analysis.requires_explanation = self._requires_explanation(analysis)
        analysis.requires_data = self._requires_data(analysis)
        analysis.requires_action = self._requires_action(analysis)
        
        # Map to intent
        analysis.intent = self._map_to_intent(analysis)
        analysis.confidence = self._calculate_confidence(analysis)
        
        return analysis
    
    def _extract_verbs(self, text: str) -> List[Tuple[str, VerbCategory]]:
        """Extract verbs and categorize them."""
        verbs = []
        found_categories = set()  # Track found categories to avoid duplicates
        
        # Sort by category priority (COMMAND > QUERY > EXPLANATION > CONFIRMATION)
        category_priority = [
            VerbCategory.COMMAND,
            VerbCategory.QUERY,
            VerbCategory.EXPLANATION,
            VerbCategory.CONFIRMATION,
            VerbCategory.NEGATION,
        ]
        
        for category in category_priority:
            if category in found_categories:
                continue
                
            verb_list = self.VERB_MAPPINGS.get(category, [])
            for verb in verb_list:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(verb) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    verbs.append((verb, category))
                    found_categories.add(category)
                    break  # Only one verb per category
        
        return verbs
    
    def _extract_connectors(self, text: str) -> List[Tuple[str, ConnectorType]]:
        """Extract connecting words and categorize them."""
        connectors = []
        
        for conn_type, conn_list in self.CONNECTOR_MAPPINGS.items():
            for connector in conn_list:
                # Use word boundaries for connectors too
                pattern = r'\b' + re.escape(connector) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    connectors.append((connector, conn_type))
                    break
        
        return connectors
    
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
        
        # Check for explanation keywords
        explanation_keywords = ['por que', 'pq', 'porque', 'como', 'why', 'how', 'explain']
        text_lower = analysis.main_verb or ""
        if any(kw in text_lower for kw in explanation_keywords):
            return True
        
        return False
    
    def _requires_data(self, analysis: LinguisticAnalysis) -> bool:
        """Determine if user requires data/information."""
        if analysis.verb_category == VerbCategory.QUERY:
            return True
        
        query_keywords = ['quantos', 'quantas', 'quais', 'que', 'how many', 'which', 'what']
        # This would need the original text, but we can infer from verb
        return analysis.verb_category == VerbCategory.QUERY
    
    def _requires_action(self, analysis: LinguisticAnalysis) -> bool:
        """Determine if user requires action/execution."""
        return analysis.verb_category == VerbCategory.COMMAND
    
    def _map_to_intent(self, analysis: LinguisticAnalysis) -> Optional[str]:
        """Map linguistic analysis to intent type."""
        if analysis.verb_category == VerbCategory.COMMAND:
            # Further classify command type based on verbs
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
        
        # Base confidence from verb detection
        if analysis.main_verb:
            confidence += 0.4
        
        # Boost from connector detection
        if analysis.connectors:
            confidence += 0.2
        
        # Boost from clear category
        if analysis.verb_category:
            confidence += 0.2
        
        # Boost from intent mapping
        if analysis.intent:
            confidence += 0.2
        
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
            conn_str = ", ".join([f"{c[0]} ({c[1].value})" for c in analysis.connectors])
            context_parts.append(f"CONNECTORS: {conn_str}")
        
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
        
        return "\n".join(context_parts)


# Singleton instance
_linguistic_analyzer: Optional[LinguisticAnalyzer] = None


def get_linguistic_analyzer() -> LinguisticAnalyzer:
    """Get or create linguistic analyzer instance."""
    global _linguistic_analyzer
    if _linguistic_analyzer is None:
        _linguistic_analyzer = LinguisticAnalyzer()
    return _linguistic_analyzer
