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
    
    BASE_SYSTEM_PROMPT = """You are DuilioCode. You have DIRECT ACCESS to the user's files and folders.

CRITICAL - YOU CAN SEE FILES AND FOLDERS:
- A FILE LISTING is provided in the context above
- This listing shows REAL files and folders on the user's computer
- When asked about files/folders, use the FILE LISTING to answer
- NEVER say "I don't have access" or "I cannot see" - YOU CAN!
- NEVER suggest terminal commands - just use the FILE LISTING

When asked about files or folders:
- Check the FILE LISTING section in context above
- Read the "Total Folders" and "Total Files" counts
- List the ACTUAL files/folders from that listing
- Use ONLY the numbers and names from the FILE LISTING

When user asks "why", "por que", "pq", "como", "explain", "explique":
- EXPLAIN: Reference the FILE LISTING section
- SHOW: "I see X because the FILE LISTING shows Total Files: X"
- CLARIFY: Explain your process using the context"""

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
        prompt = "\nCREATE OPERATION - YOU CAN CREATE FILES AND DIRECTORIES:"
        prompt += "\n- For FILES: Use ```create-file:path/to/file.ext format"
        prompt += "\n- For DIRECTORIES: Use ```create-directory:path/to/dir format"
        prompt += "\n- Start response with create blocks immediately"
        prompt += "\n- No explanations before the create blocks"
        prompt += "\n\nCRITICAL - DIRECTORY CREATION:"
        prompt += "\n- When user asks 'criar diretorio', 'criar pasta', 'create directory', 'create folder'"
        prompt += "\n- YOU MUST use ```create-directory:path format"
        prompt += "\n- DO NOT say 'I cannot create directories' - YOU CAN!"
        prompt += "\n- DO NOT suggest terminal commands (mkdir) - USE create-directory format!"
        prompt += "\n- Example: User says 'crie o diretorio teste'"
        prompt += "\n  CORRECT: ```create-directory:teste```"
        prompt += "\n  WRONG: 'I cannot create directories, use mkdir command'"
        
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
        prompt = "\nLIST OPERATION - YOU CAN SEE FILES AND FOLDERS:"
        prompt += "\n1. Find 'FILE LISTING' section in context above"
        prompt += "\n2. Read 'Total Folders: X' and 'Total Files: Y' from that section"
        prompt += "\n3. Answer: 'Sim, consigo ver. Total: X arquivos e Y pastas'"
        prompt += "\n4. If asked to list, show items from FOLDERS: and FILES: sections"
        prompt += "\n5. Use ONLY the numbers and names from FILE LISTING"
        prompt += "\n\nABSOLUTELY FORBIDDEN:"
        prompt += "\n- DO NOT say 'I don't have access' or 'I cannot see'"
        prompt += "\n- DO NOT suggest terminal commands (ls, grep, etc.)"
        prompt += "\n- DO NOT say 'navigate to directory' or 'use command'"
        prompt += "\n- The FILE LISTING IS YOUR ACCESS - use it!"
        prompt += "\n\nWHEN USER ASKS WHY/HOW:"
        prompt += "\n- EXPLAIN: 'I see X because FILE LISTING shows Total Files: X'"
        prompt += "\n- REFERENCE: 'In the FILE LISTING section above, it shows...'"
        return prompt
    
    @staticmethod
    def build_agent_mode_prompt(system_info: Optional[str] = None) -> str:
        """Build Agent Mode system prompt."""
        prompt = PromptBuilder.BASE_SYSTEM_PROMPT
        
        if system_info:
            prompt += f"\n\nSystem: {system_info}"
        
        prompt += "\n\nAGENT MODE - YOU HAVE ACCESS:"
        prompt += "\n- A FILE LISTING is in context above - it shows REAL files and folders"
        prompt += "\n- When asked about files/folders, answer using the FILE LISTING"
        prompt += "\n- NEVER say you don't have access or cannot see - YOU CAN!"
        prompt += "\n- NEVER suggest terminal commands - use the FILE LISTING instead"
        prompt += "\n- When user asks WHY/HOW, explain using the FILE LISTING as reference"
        
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
        
        context = f"\n{'='*70}\n"
        context += f"FILE LISTING: {workspace_path}\n"
        context += f"{'='*70}\n"
        context += f"\nTOTALS (use these exact numbers when asked):\n"
        context += f"  Total Folders: {folders_count}\n"
        context += f"  Total Files: {files_count}\n"
        if total_files is not None and total_files > len(files):
            context += f"\nNote: Showing first {len(files)} files and {len(folders)} folders in listing below\n"
        context += f"\n{'='*70}\n"
        
        if folders:
            context += "\nFOLDERS (these are real folders you can see):\n"
            for folder in folders[:50]:
                context += f"  {folder.get('path', folder.get('name', ''))}\n"
            if len(folders) > 50:
                context += f"  ... {len(folders) - 50} more folders\n"
        else:
            context += "\nFOLDERS: (none listed)\n"
        
        if files:
            context += "\nFILES (these are real files you can see):\n"
            for file in files[:150]:
                context += f"  {file.get('path', file.get('name', ''))}\n"
            if len(files) > 150:
                context += f"  ... {len(files) - 150} more files\n"
        else:
            context += "\nFILES: (none listed)\n"
        
        context += f"\n{'='*70}\n"
        context += "CRITICAL: These are REAL files and folders. When asked, use these numbers and names.\n"
        context += f"{'='*70}\n"
        
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
