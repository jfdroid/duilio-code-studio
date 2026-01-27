"""
Prompt Builder Service
======================
Builds clean, efficient prompts based on best practices for Ollama/LLM.
Separates concerns: CRUD operations, file operations, system info.
"""

from typing import Dict, List, Optional, Any
from enum import Enum


class OperationType(Enum):
    """CRUD operation types."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class PromptBuilder:
    """
    Builds optimized prompts for Ollama based on best practices.
    
    Principles:
    - Direct, imperative language
    - Operation-specific prompts
    - Minimal verbosity
    - Clear context structure
    """
    
    BASE_SYSTEM_PROMPT = """You are DuilioCode. You have access to the user's files.

When asked about files:
- Check the FILE LISTING in context above
- List the ACTUAL files from that listing
- Never say you cannot see files
- Never invent paths like "/path/to/directory"
- Use ONLY the file names from the context

When user asks "why", "por que", "pq", "como", "explain", "explique", "motivo", "razão":
- EXPLAIN your reasoning and decisions
- Show HOW you arrived at the answer
- Reference the FILE LISTING or context you used
- Be clear about your process"""

    @staticmethod
    def build_crud_prompt(operation: OperationType, context: Dict[str, Any]) -> str:
        """
        Build operation-specific CRUD prompt.
        
        Based on best practices:
        - Specific instructions per operation
        - Direct imperative language
        - Clear format requirements
        """
        prompts = {
            OperationType.CREATE: PromptBuilder._build_create_prompt(context),
            OperationType.READ: PromptBuilder._build_read_prompt(context),
            OperationType.UPDATE: PromptBuilder._build_update_prompt(context),
            OperationType.DELETE: PromptBuilder._build_delete_prompt(context),
            OperationType.LIST: PromptBuilder._build_list_prompt(context),
        }
        return prompts.get(operation, "")
    
    @staticmethod
    def _build_create_prompt(context: Dict[str, Any]) -> str:
        """Build CREATE operation prompt."""
        prompt = "\nCREATE:"
        prompt += "\n- Use ```create-file:path/to/file.ext format"
        prompt += "\n- Start response with create-file blocks immediately"
        prompt += "\n- No explanations before the create-file blocks"
        
        if context.get("project_type"):
            project_name = context.get('project_name', 'project')
            prompt += f"\n- Project: {context['project_type']}"
            prompt += f"\n- Create directory: ```create-directory:{project_name}```"
            prompt += f"\n- Then files: ```create-file:{project_name}/file.ext```"
        
        return prompt
    
    @staticmethod
    def _build_read_prompt(context: Dict[str, Any]) -> str:
        """Build READ operation prompt."""
        prompt = "\nREAD:"
        prompt += "\n- File content is in context above"
        prompt += "\n- Explain what is written in the file"
        prompt += "\n- Do NOT use create-file or modify-file formats"
        return prompt
    
    @staticmethod
    def _build_update_prompt(context: Dict[str, Any]) -> str:
        """Build UPDATE operation prompt."""
        prompt = "\nUPDATE:"
        prompt += "\n- Use ```modify-file:path/to/file.ext format"
        prompt += "\n- Read file content from context first"
        prompt += "\n- Show complete modified content (not just changes)"
        return prompt
    
    @staticmethod
    def _build_delete_prompt(context: Dict[str, Any]) -> str:
        """Build DELETE operation prompt."""
        prompt = "\nDELETE:"
        prompt += "\n- Use ```delete-file:path or ```delete-directory:path format"
        prompt += "\n- Only delete if user explicitly requests it"
        prompt += "\n- Be careful with deletions"
        return prompt
    
    @staticmethod
    def _build_list_prompt(context: Dict[str, Any]) -> str:
        """Build LIST operation prompt."""
        prompt = "\nLIST OPERATION:"
        prompt += "\n1. Find 'FILE LISTING' section in context above"
        prompt += "\n2. Read the 'Total Folders' and 'Total Files' counts from that section"
        prompt += "\n3. Answer with those EXACT numbers: 'Total: X arquivos e Y pastas'"
        prompt += "\n4. If asked to list files, show the files from the FILES: section"
        prompt += "\n5. Use ONLY the numbers and names from the FILE LISTING context"
        prompt += "\n\nWHEN USER ASKS WHY/HOW (por que, pq, como, explain):"
        prompt += "\n- EXPLAIN: 'I see X files because I counted them from the FILE LISTING section above'"
        prompt += "\n- SHOW: Reference the exact section: 'In the FILE LISTING, it shows Total Files: X'"
        prompt += "\n- CLARIFY: Explain if it's a sample listing vs total count"
        prompt += "\n\nCRITICAL:"
        prompt += "\n- The FILE LISTING shows the REAL counts - use them!"
        prompt += "\n- Never invent numbers or paths"
        prompt += "\n- Never say you cannot see - the listing is in context!"
        return prompt
    
    @staticmethod
    def build_agent_mode_prompt(system_info: Optional[str] = None) -> str:
        """Build Agent Mode system prompt."""
        prompt = PromptBuilder.BASE_SYSTEM_PROMPT
        
        if system_info:
            prompt += f"\n\nSystem: {system_info}"
        
        prompt += "\n\nAGENT MODE:"
        prompt += "\n- File listing is in context above"
        prompt += "\n- When asked about files, LIST them from the context"
        prompt += "\n- When user asks WHY/HOW/EXPLAIN, provide detailed reasoning"
        prompt += "\n- Explain your decisions: reference the FILE LISTING, show your process"
        prompt += "\n- Balance: direct answers for simple questions, explanations when asked"
        
        return prompt
    
    @staticmethod
    def build_file_listing_context(
        files: List[Dict], 
        folders: List[Dict], 
        workspace_path: str,
        total_files: Optional[int] = None,
        total_folders: Optional[int] = None
    ) -> str:
        """Build file listing context in clean format."""
        # Use accurate totals if provided, otherwise use listed counts
        files_count = total_files if total_files is not None else len(files)
        folders_count = total_folders if total_folders is not None else len(folders)
        
        context = f"\nFILE LISTING: {workspace_path}\n"
        context += f"Total Folders: {folders_count}, Total Files: {files_count}\n"
        if total_files is not None and total_files > len(files):
            context += f"(Showing first {len(files)} files in listing below)\n"
        context += "\n"
        
        if folders:
            context += "FOLDERS:\n"
            for folder in folders[:50]:
                context += f"  {folder.get('path', folder.get('name', ''))}\n"
            if len(folders) > 50:
                context += f"  ... {len(folders) - 50} more\n"
        
        if files:
            context += "\nFILES:\n"
            for file in files[:150]:
                context += f"  {file.get('path', file.get('name', ''))}\n"
            if len(files) > 150:
                context += f"  ... {len(files) - 150} more\n"
        
        return context
    
    @staticmethod
    def build_full_prompt(
        system_prompt: str,
        context_parts: List[str],
        user_messages: List[str],
        operation: Optional[OperationType] = None
    ) -> str:
        """
        Build complete prompt with optimal structure.
        
        Structure (best practice):
        1. File listing (if available) - highest priority
        2. Other context
        3. User messages
        4. Operation-specific instructions
        """
        # Separate file listing from other context
        file_listing = [c for c in context_parts if "FILE LISTING" in c]
        other_context = [c for c in context_parts if c not in file_listing]
        
        prompt = system_prompt
        
        # Add file listing first (highest priority)
        if file_listing:
            prompt += "\n\n" + "\n".join(file_listing)
        
        # Add other context
        if other_context:
            prompt += "\n\n" + "\n".join(other_context)
        
        # Add operation-specific prompt
        if operation:
            prompt += PromptBuilder.build_crud_prompt(operation, {})
        
        # Add user messages
        prompt += "\n\n---\n\n"
        prompt += "\n".join(user_messages)
        prompt += "\n\nAssistant:"
        
        return prompt
