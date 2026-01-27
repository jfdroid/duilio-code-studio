/**
 * DuilioCode Studio - Chat Module
 * AI assistant chat interface
 */

const Chat = {
    abortController: null,
    mode: 'chat', // 'chat' (simple) or 'agent' (complex with codebase)

    /**
     * Initialize chat mode from HTML
     */
    initMode() {
        // Check which button is active in HTML
        const agentBtn = document.getElementById('agentModeBtn');
        if (agentBtn && agentBtn.classList.contains('active')) {
            this.mode = 'agent';
            console.log('[DuilioCode] Initialized mode: agent (from HTML)');
        } else {
            this.mode = 'chat';
            console.log('[DuilioCode] Initialized mode: chat (from HTML)');
        }
        
        // Set default model for initial mode
        // Wait a bit for models to load
        setTimeout(() => {
            this.setDefaultModelForMode(this.mode);
        }, 500);
    },

    /**
     * Set default model based on mode
     */
    setDefaultModelForMode(mode) {
        const modelSelect = document.getElementById('modelSelect');
        if (!modelSelect) return;
        
        // Get available models
        const availableModels = Array.from(modelSelect.options).map(opt => opt.value);
        
        if (mode === 'chat') {
            // Chat mode: Try to find Llama model
            const llamaModel = availableModels.find(m => 
                m.toLowerCase().includes('llama') || 
                m.toLowerCase().includes('llama2') ||
                m.toLowerCase().includes('llama3')
            );
            
            if (llamaModel) {
                modelSelect.value = llamaModel;
                AppState.chat.currentModel = llamaModel;
                console.log('[DuilioCode] Chat mode: Set default model to', llamaModel);
            } else {
                console.warn('[DuilioCode] Chat mode: Llama model not found, keeping current selection');
            }
        } else {
            // Agent mode: Try to find Qwen 7B
            const qwen7bModel = availableModels.find(m => 
                m.toLowerCase().includes('qwen') && 
                (m.toLowerCase().includes('7b') || m.toLowerCase().includes('7-b'))
            );
            
            if (qwen7bModel) {
                modelSelect.value = qwen7bModel;
                AppState.chat.currentModel = qwen7bModel;
                console.log('[DuilioCode] Agent mode: Set default model to', qwen7bModel);
            } else {
                // Fallback to any Qwen model
                const qwenModel = availableModels.find(m => m.toLowerCase().includes('qwen'));
                if (qwenModel) {
                    modelSelect.value = qwenModel;
                    AppState.chat.currentModel = qwenModel;
                    console.log('[DuilioCode] Agent mode: Set default model to', qwenModel, '(7B not found)');
                } else {
                    console.warn('[DuilioCode] Agent mode: Qwen model not found, keeping current selection');
                }
            }
        }
    },

    /**
     * Set chat mode
     */
    setMode(mode) {
        this.mode = mode;
        
        // Update UI
        const chatBtn = document.getElementById('chatModeBtn');
        const agentBtn = document.getElementById('agentModeBtn');
        
        if (chatBtn) chatBtn.classList.toggle('active', mode === 'chat');
        if (agentBtn) {
            agentBtn.classList.toggle('active', mode === 'agent');
            agentBtn.dataset.mode = mode === 'agent' ? 'agent' : '';
        }
        
        // Update placeholder
        const input = document.getElementById('chatInput');
        if (input) {
            input.placeholder = mode === 'agent' 
                ? 'Ask me to create files, run commands, modify code...'
                : 'Ask me anything, I\'ll explain and suggest...';
        }
        
        // Set default model based on mode
        this.setDefaultModelForMode(mode);
        
        // === CHAT MODE: Centered Layout (like Gemini/DeepSeek) ===
        // Center chat and hide all IDE elements in Chat mode
        const explorerPanel = document.getElementById('explorerPanel');
        const sidebar = document.querySelector('.sidebar-panels');
        const mainContent = document.querySelector('.main-content-wrapper');
        const mainArea = document.querySelector('.main-area');
        const chatPanel = document.getElementById('chatPanel');
        const tabsBar = document.getElementById('tabsBar');
        const editorPanel = document.getElementById('editorPanel');
        const statusBar = document.querySelector('.status-bar');
        const activityBar = document.querySelector('.activity-bar');
        
        if (mode === 'chat') {
            // Chat mode: Centered, focused layout
            if (explorerPanel) explorerPanel.classList.add('hidden');
            if (sidebar) sidebar.classList.add('hidden');
            if (mainContent) mainContent.classList.add('chat-mode-centered');
            if (mainArea) mainArea.classList.add('hidden');
            if (tabsBar) tabsBar.classList.add('hidden');
            if (editorPanel) editorPanel.classList.add('hidden');
            if (activityBar) activityBar.classList.add('hidden');
            if (statusBar) statusBar.classList.add('hidden');
            if (chatPanel) {
                chatPanel.classList.add('chat-centered');
                chatPanel.style.width = '100%';
                chatPanel.style.maxWidth = '900px';
                chatPanel.style.margin = '0 auto';
            }
            
            console.log('[DuilioCode] Chat mode: Centered layout activated');
        } else {
            // Agent mode: Show explorer and full IDE layout
            if (explorerPanel) explorerPanel.classList.remove('hidden');
            if (sidebar) sidebar.classList.remove('hidden');
            if (mainContent) mainContent.classList.remove('chat-mode-centered');
            if (mainArea) mainArea.classList.remove('hidden');
            if (tabsBar) tabsBar.classList.remove('hidden');
            if (editorPanel) editorPanel.classList.remove('hidden');
            if (activityBar) activityBar.classList.remove('hidden');
            if (statusBar) statusBar.classList.remove('hidden');
            if (chatPanel) {
                chatPanel.classList.remove('chat-centered');
                chatPanel.style.width = '';
                chatPanel.style.maxWidth = '';
                chatPanel.style.margin = '';
            }
            
            console.log('[DuilioCode] Agent mode: Full IDE layout activated');
        }
        
        Utils.showNotification(`Mode: ${mode === 'agent' ? 'Agent (Execute Actions)' : 'Chat (Conversation Only)'}`, 'info');
    },

    /**
     * Send message to AI
     */
    async send() {
        console.log('[DuilioCode] Chat.send() called');
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        // CRITICAL: Re-check mode from UI state (in case it changed)
        const agentBtn = document.getElementById('agentModeBtn');
        const chatBtn = document.getElementById('chatModeBtn');
        if (agentBtn && agentBtn.classList.contains('active')) {
            this.mode = 'agent';
        } else if (chatBtn && chatBtn.classList.contains('active')) {
            this.mode = 'chat';
        }
        
        console.log('[DuilioCode] Message:', message, 'isLoading:', AppState.chat.isLoading, 'mode:', this.mode);
        
        if (!message || AppState.chat.isLoading) {
            console.log('[DuilioCode] Blocked: empty message or already loading');
            return;
        }
        
        // Add user message
        this.addMessage('user', message);
        if (typeof ChatHistory !== 'undefined') {
            ChatHistory.addMessage('user', message);
        }
        input.value = '';
        input.style.height = 'auto';
        
        // Show loading and stop button
        AppState.setLoading(true);
        this.showTypingIndicator();
        this.toggleStopButton(true);
        
        // Create abort controller for cancellation
        this.abortController = new AbortController();
        
        try {
            // Build comprehensive context
            let context = '';
            const workspacePath = AppState.workspace.currentPath;
            
            // Add workspace context
            if (workspacePath) {
                context += `Current workspace: ${workspacePath}\n`;
            }
            
            // Add file context if file is open
            if (AppState.editor.currentFile) {
                // Get content from Monaco or fallback textarea
                let content = '';
                if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                    content = MonacoEditor.getContent();
                } else {
                    content = document.getElementById('codeEditor')?.value || '';
                }
                context += `\n=== CURRENTLY OPEN FILE ===\n`;
                context += `File: ${AppState.editor.currentFile.path}\n`;
                context += `Language: ${AppState.editor.currentFile.language}\n`;
                context += `Content (first 2000 chars):\n\`\`\`${AppState.editor.currentFile.language}\n${content.slice(0, 2000)}\n\`\`\`\n`;
            }
            
            // Build system context
            // NOTE: The backend will automatically include codebase analysis when include_codebase: true
            // We add instructions here to guide the AI on how to use that context
            let systemContext = '';
            if (workspacePath) {
                systemContext += `You have access to the user's workspace at: ${workspacePath}\n`;
                systemContext += `The backend will provide you with FULL CODEBASE ANALYSIS including:\n`;
                systemContext += `- Project structure and file tree\n`;
                systemContext += `- Key files with their content\n`;
                systemContext += `- Dependencies and entry points\n`;
                systemContext += `- Coding patterns and conventions\n\n`;
                systemContext += `You MUST use this analysis to make intelligent decisions when creating files.\n`;
            }
            if (context) {
                systemContext += context;
            }
            
            const finalSystemContext = systemContext || null;
            
            // Get selected model (required - no auto selection)
            const selectedModel = document.getElementById('modelSelect')?.value;
            if (!selectedModel) {
                throw new Error('No model selected. Please select a model first.');
            }
            const modelToUse = selectedModel;
            
            // Add mode to context with CRITICAL instructions for file creation
            const modeContext = this.mode === 'agent' 
                ? `\n\n=== AGENT MODE - CRITICAL INSTRUCTIONS ===

You are in AGENT MODE. When the user asks to create files, modify code, or run commands, you MUST output the actual actions in a structured format.

BEFORE CREATING ANY FILE:
1. ANALYZE the codebase structure provided in the context above
2. UNDERSTAND the project's architecture, patterns, and conventions
3. IDENTIFY where similar files are located in the project
4. FOLLOW existing directory structures and naming conventions
5. MATCH the coding style, imports, and structure of similar files
6. RESPECT framework-specific patterns (React, Python, Node.js, etc.)
7. CREATE files in the CORRECT directories based on their purpose and type
8. ENSURE new files integrate properly with existing code (imports, exports, dependencies)

FILE CREATION FORMAT (CRITICAL - USE THIS EXACT FORMAT):
\`\`\`create-file:path/to/file.ext
file content here
\`\`\`

IMPORTANT: You can create MULTIPLE files in ONE response by using multiple \`\`\`create-file: blocks.
When user asks for a "project" or "complete application", create ALL necessary files in the SAME response.

PATH RULES (CRITICAL):
- CRITICAL: When user asks for a file WITHOUT specifying a directory (e.g., "create utils.js"), create it in the ROOT of the workspace (e.g., utils.js, NOT src/utils.js)
- ONLY create files in subdirectories if:
  * User explicitly specifies a directory (e.g., "create src/utils.js")
  * The codebase already has a clear structure and similar files exist in that directory
  * You're creating a complete project with multiple files and following established patterns
- For simple single-file requests, ALWAYS use root unless user specifies otherwise
- For files INSIDE the workspace: Use RELATIVE paths from workspace root
- For files OUTSIDE the workspace (when user explicitly requests): Use ABSOLUTE paths (e.g., /Users/username/Desktop/file.txt, ~/Documents/file.txt)
- If user asks to create a file in a specific location (Desktop, Documents, etc.), use the FULL ABSOLUTE PATH they requested
- If creating a component/module/test and similar files exist, follow their pattern
- NEVER create files randomly - always base on codebase analysis (for workspace files) or user's explicit request (for external paths)

CONTENT RULES:
- When user asks to create a file "based on", "similar to", "like", or "following the pattern of" another file:
  * Find similar files in the codebase (same type, same directory, similar name)
  * Use those files as REFERENCE and TEMPLATE
  * Match the EXACT structure, imports, exports, and patterns from the reference files
  * Keep the same coding style, naming conventions, and organization
  * Adapt the content to the new file's purpose while maintaining consistency
- Match the coding style of similar files in the project
- Include proper imports/exports matching project patterns
- Follow the same structure and organization as existing files
- Use the same naming conventions (camelCase, PascalCase, snake_case, etc.)
- Include proper headers, comments, and documentation if the project uses them
- Match indentation style (spaces vs tabs, 2 vs 4 spaces)
- When creating files similar to existing ones, analyze the reference files' content in the codebase context and replicate their patterns

For modifying files:
\`\`\`modify-file:path/to/file.ext
new content
\`\`\`

For running commands:
\`\`\`run-command
command here
\`\`\`

CONTEXT RETENTION:
- Remember ALL files created in previous messages in this conversation
- When user refers to "that file" or "the file we created", remember which file they mean
- Maintain full conversation context - you have access to all previous messages
- When modifying files, reference the file by its path from previous context

REMEMBER: You have FULL CONTEXT of the codebase. Use it to make intelligent decisions about file placement and structure.
When creating files "based on" or "similar to" existing files, use their FULL CONTENT from the codebase context as a TEMPLATE.`
                : '\n\nYou are in CHAT MODE. Just explain, suggest, and discuss. Do not execute any actions.';
            
            const fullContext = (finalSystemContext || '') + modeContext;
            
            // MODE-BASED ENDPOINT SELECTION:
            // - Chat mode → Simple endpoint (/api/chat/simple) - clean Ollama connection
            // - Agent mode → Complex endpoint (/api/chat) - full features with codebase
            let response;
            if (this.mode === 'chat') {
                // CHAT MODE: Simple, direct Ollama connection - no complex logic
                console.log('[DuilioCode] CHAT mode - using simple endpoint');
                const messages = AppState.chat.messages.map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));
                // Add current user message
                messages.push({ role: 'user', content: message });
                
                response = await API.chatSimple(messages, modelToUse, 0.7, false);
                console.log('[DuilioCode] Simple API Response:', response);
            } else {
                // AGENT MODE: Complex endpoint with full features
                console.log('[DuilioCode] AGENT mode - using complex endpoint with codebase');
                console.log('[DuilioCode] Workspace from AppState:', AppState.workspace.currentPath);
                console.log('[DuilioCode] Workspace variable:', workspacePath);
                console.log('[DuilioCode] Context length:', fullContext?.length || 0);
                
                // Build messages for complex endpoint
                const messages = AppState.chat.messages.map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));
                messages.push({ role: 'user', content: message });
                
                // CRITICAL: Ensure workspace_path is sent in Agent mode
                // Use AppState directly to ensure we have the latest value
                const finalWorkspacePath = AppState.workspace.currentPath || workspacePath;
                console.log('[DuilioCode] Final workspace_path to send:', finalWorkspacePath);
                
                if (!finalWorkspacePath) {
                    console.warn('[DuilioCode] WARNING: No workspace_path available in Agent mode!');
                    console.warn('[DuilioCode] This may cause file listing to fail.');
                    Utils.showNotification('Warning: No workspace folder open. File operations may not work.', 'warning');
                }
                
                response = await API.chat(messages, modelToUse, false);
                console.log('[DuilioCode] Complex API Response:', response);
            }
            
            // Log which model was used
            if (response.model) {
                console.log(`[DuilioCode] Using model: ${response.model}`);
            }
            
            this.hideTypingIndicator();
            
            // Extract response text (handle both simple and complex response formats)
            let responseText;
            if (response.choices && response.choices[0] && response.choices[0].message) {
                // Both modes use choices[0].message.content format
                responseText = response.choices[0].message.content;
            } else if (response.response) {
                // Fallback: old format
                responseText = response.response;
            } else {
                console.warn('[DuilioCode] Unexpected response format:', response);
                responseText = JSON.stringify(response);
            }
            
            // In Agent mode, process and execute actions from response
            if (this.mode === 'agent') {
                responseText = await this.processAgentActions(responseText);
            }
            
            this.addMessage('assistant', responseText);
            if (typeof ChatHistory !== 'undefined') {
                ChatHistory.addMessage('assistant', responseText);
            }
            
            // CRITICAL: Refresh explorer if actions were processed (Agent mode only)
            if (this.mode === 'agent' && response.actions_processed && response.actions_result) {
                if (response.actions_result.success_count > 0 || response.refresh_explorer) {
                    console.log('[DuilioCode] Refreshing explorer after actions');
                    if (typeof Workspace !== 'undefined') {
                        await Workspace.refresh();
                    }
                }
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            if (error.name === 'AbortError') {
                this.addMessage('assistant', 'Generation stopped.');
            } else {
                // Properly handle error object
                let errorMsg = 'Unknown error';
                if (typeof error === 'string') {
                    errorMsg = error;
                } else if (error.message) {
                    errorMsg = error.message;
                } else if (error.detail) {
                    errorMsg = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
                }
                this.addMessage('assistant', `Error: ${errorMsg}`);
                console.error('[DuilioCode] Chat error:', error);
            }
        } finally {
            AppState.setLoading(false);
            this.toggleStopButton(false);
            this.abortController = null;
        }
    },

    /**
     * Stop current generation
     */
    stop() {
        if (this.abortController) {
            this.abortController.abort();
            this.hideTypingIndicator();
            this.toggleStopButton(false);
            AppState.setLoading(false);
        }
    },

    /**
     * Toggle stop button visibility
     */
    toggleStopButton(show) {
        const sendBtn = document.getElementById('sendBtn');
        const stopBtn = document.getElementById('stopBtn');
        if (sendBtn) sendBtn.style.display = show ? 'none' : 'flex';
        if (stopBtn) stopBtn.style.display = show ? 'flex' : 'none';
    },
    
    /**
     * Add message to chat
     */
    addMessage(role, content) {
        const container = document.getElementById('chatMessages');
        const time = Utils.formatTime();
        
        const avatarContent = role === 'user' 
            ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
            : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';
        
        const messageHtml = `
            <div class="message">
                <div class="message-header">
                    <div class="message-avatar ${role}">${avatarContent}</div>
                    <span class="message-sender">${role === 'user' ? 'You' : 'DuilioCode'}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-content">${this.formatMessage(content)}</div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', messageHtml);
        container.scrollTop = container.scrollHeight;
        
        // CRITICAL: Attach event listeners AFTER DOM insertion
        // Use setTimeout to ensure DOM is fully ready
        setTimeout(() => {
            const lastMessage = container.lastElementChild;
            if (lastMessage) {
                // File links - use event delegation for better reliability
                const messageContent = lastMessage.querySelector('.message-content');
                if (messageContent) {
                    // Remove any existing listeners by cloning (clean slate)
                    const fileLinks = messageContent.querySelectorAll('.file-link[data-file-path]');
                    fileLinks.forEach(link => {
                        // Remove old listeners by replacing the element
                        const newLink = link.cloneNode(true);
                        link.parentNode.replaceChild(newLink, link);
                        
                        // Add fresh event listener
                        newLink.addEventListener('click', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            const filePath = newLink.getAttribute('data-file-path');
                            console.log('[Chat] File link clicked:', filePath);
                            if (filePath) {
                                Chat.openFileFromChat(filePath);
                            }
                        });
                        
                        // Ensure link is clickable
                        newLink.style.cursor = 'pointer';
                        newLink.style.textDecoration = 'underline';
                    });
                    
                    // Code block headers
                    const codeHeaders = messageContent.querySelectorAll('.code-block-header[data-file-path]');
                    codeHeaders.forEach(header => {
                        // Remove old listeners
                        const newHeader = header.cloneNode(true);
                        header.parentNode.replaceChild(newHeader, header);
                        
                        // Add fresh event listener
                        newHeader.addEventListener('click', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            const filePath = newHeader.getAttribute('data-file-path');
                            console.log('[Chat] Code header clicked:', filePath);
                            if (filePath) {
                                Chat.openFileFromChat(filePath);
                            }
                        });
                        
                        // Ensure header is clickable
                        newHeader.style.cursor = 'pointer';
                    });
                }
            }
        }, 0);
        
        // Highlight code blocks (skip create-file and modify-file blocks)
        if (typeof hljs !== 'undefined') {
            container.querySelectorAll('pre code').forEach(block => {
                // Skip highlighting for create-file and modify-file blocks
                const text = block.textContent || '';
                if (text.includes('create-file:') || text.includes('modify-file:')) {
                    return;
                }
                try {
                    hljs.highlightElement(block);
                } catch (error) {
                    // Ignore highlighting errors (e.g., unknown language)
                    console.debug('[Chat] Highlight error:', error);
                }
            });
        }
        
        // Render Mermaid diagrams
        if (typeof ChatRenderers !== 'undefined') {
            ChatRenderers.renderMermaidDiagrams(container);
        }
        
        AppState.addMessage({ role, content, time });
    },
    
    /**
     * Format message content (markdown-like)
     * - Makes file paths clickable
     * - Adds clickable headers to code blocks
     * - Renders Mermaid diagrams and KaTeX math
     */
    formatMessage(content) {
        let formatted = content;
        
        // CRITICAL: Make file paths clickable BEFORE markdown parsing
        // This ensures paths are converted to links before marked.parse() processes them
        formatted = this.makePathsClickable(formatted);
        
        // Use marked for markdown if available
        if (typeof marked !== 'undefined') {
            formatted = marked.parse(formatted);
            // After marked.parse, paths might be inside <p> tags, re-process them
            formatted = this.makePathsClickable(formatted);
        } else {
            // Basic formatting
            formatted = formatted
                .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                    return `<pre><code class="language-${lang}">${Utils.escapeHtml(code.trim())}</code><button class="apply-code-btn" onclick="Chat.applyCode(this)">Apply</button></pre>`;
                })
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }
        
        // Process Mermaid and KaTeX
        if (typeof ChatRenderers !== 'undefined') {
            formatted = ChatRenderers.processContent(formatted);
        }
        
        // Add clickable headers to code blocks (after markdown processing)
        formatted = this.addCodeBlockHeaders(formatted);
        
        return formatted;
    },
    
    /**
     * Make file paths in text clickable
     * Detects patterns like: src/App.js, ./components/Button.tsx, etc.
     */
    makePathsClickable(html) {
        // Pattern to match file paths (not already in links)
        // Updated to match paths even inside markdown paragraphs
        const pathPattern = /(?<!["'=])(\b(?:\.\/|\.\.\/|src\/|app\/|lib\/|components\/|services\/|utils\/|pages\/|api\/|tests?\/)?[\w\-./]+\.(js|jsx|ts|tsx|py|java|kt|go|rs|rb|c|cpp|h|hpp|css|scss|html|json|yaml|yml|md|txt|sh|sql))\b(?![^<]*>)/gi;
        
        return html.replace(pathPattern, (match, path) => {
            // Skip if it's a URL or already linked
            if (path.startsWith('http') || path.includes('://')) return match;
            
            // CRITICAL: Check if this match is already inside a link tag
            // Look backwards and forwards in the HTML string to see if we're inside <a>...</a>
            const matchIndex = html.indexOf(match);
            if (matchIndex !== -1) {
                const beforeMatch = html.substring(0, matchIndex);
                const afterMatch = html.substring(matchIndex + match.length);
                
                // Find the last <a> tag before this match
                const lastATag = beforeMatch.lastIndexOf('<a ');
                const lastATagClose = beforeMatch.lastIndexOf('</a>');
                
                // If there's an <a> tag before us and no closing </a> before us, we're inside a link
                if (lastATag > lastATagClose) {
                    return match; // Already inside a link, skip
                }
            }
            
            // Escape path for HTML attribute to prevent breaking
            const escapedPath = Utils.escapeHtml(path);
            // Use data attribute instead of inline onclick to avoid issues with special characters
            return `<a href="#" class="file-link" data-file-path="${escapedPath}" title="Open ${escapedPath}" style="cursor: pointer; text-decoration: underline; color: #4a9eff;">${path}</a>`;
        });
    },
    
    /**
     * Add clickable file headers to code blocks
     * Converts comments like "// src/App.js" to clickable headers
     */
    addCodeBlockHeaders(html) {
        // Find code blocks with file path comments at the start
        const codeBlockPattern = /<pre><code[^>]*>((?:\/\/|#|\/\*|\{\/\*)\s*([\w\-./]+\.(js|jsx|ts|tsx|py|java|kt|go|rs|rb|c|cpp|h|hpp|css|scss|html|json|yaml|yml|md))\s*(?:\*\/|\*\/\})?[\r\n])/gi;
        
        return html.replace(codeBlockPattern, (match, commentLine, filePath) => {
            // Escape path for HTML attribute
            const escapedPath = Utils.escapeHtml(filePath);
            // Create clickable header using data attribute instead of inline onclick
            const header = `<div class="code-block-header" data-file-path="${escapedPath}" title="Click to open ${escapedPath}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                <span>${filePath}</span>
            </div>`;
            
            // Replace the comment line with header
            return match.replace(commentLine, header + '<pre><code' + match.substring(match.indexOf('<code')).replace(commentLine, ''));
        });
    },
    
    /**
     * Open file from chat link
     */
    openFileFromChat(path) {
        // Normalize path - use Utils.normalizeFilePath to avoid duplication
        let fullPath = path;
        
        // Use Utils.normalizeFilePath if available (handles path normalization correctly)
        if (typeof Utils !== 'undefined' && Utils.normalizeFilePath) {
            fullPath = Utils.normalizeFilePath(path, AppState.workspace.currentPath);
        } else {
            // Fallback: only prepend workspace if path is relative
            if (path && !path.startsWith('/') && !path.startsWith('~') && AppState.workspace.currentPath) {
                // Remove leading ./ if present
                const cleanPath = path.replace(/^\.\//, '');
                // Check if path already contains workspace to avoid duplication
                if (!cleanPath.startsWith(AppState.workspace.currentPath)) {
                    fullPath = AppState.workspace.currentPath + '/' + cleanPath;
                } else {
                    fullPath = cleanPath;
                }
            }
        }
        
        console.log('[DuilioCode] Opening file from chat:', fullPath);
        
        // Try to open the file using FileManager (the correct module name)
        if (typeof FileManager !== 'undefined' && FileManager.open) {
            FileManager.open(fullPath);
            Utils.showNotification(`Opening ${path}...`, 'info');
        } else {
            console.error('[DuilioCode] FileManager not available');
            Utils.showNotification(`Cannot open: ${path}`, 'error');
        }
    },
    
    /**
     * Process agent actions from AI response
     * Extracts and executes: create-file, modify-file, run-command
     */
    async processAgentActions(responseText) {
        let processedText = responseText;
        let actionsExecuted = [];
        
        // Process create-file actions
        // Improved regex to handle paths with spaces, special chars, and multiple files
        const createFileRegex = /```create-file:([^\n]+)\n([\s\S]*?)```/g;
        let match;
        
        while ((match = createFileRegex.exec(responseText)) !== null) {
            const filePath = match[1].trim();
            const content = match[2];
            
            try {
                // CRITICAL: Normalize path to avoid duplication
                // BUT: If path is absolute and clearly outside workspace, preserve it
                const workspacePath = AppState.workspace.currentPath;

                console.log('[DuilioCode Agent] ===== FILE CREATION =====');
                console.log('[DuilioCode Agent] Original path from AI:', filePath);
                console.log('[DuilioCode Agent] Workspace path:', workspacePath);

                // Check if path is absolute and outside workspace
                let fullPath;
                if (filePath.startsWith('/') && workspacePath && !filePath.startsWith(workspacePath)) {
                    // Absolute path outside workspace - use as-is (e.g., /Users/username/Desktop/file.txt)
                    console.log('[DuilioCode Agent] Path is absolute and outside workspace - using as-is');
                    fullPath = filePath;
                } else {
                    // Normalize path (handles relative paths and paths within workspace)
                    fullPath = Utils.normalizeFilePath(filePath, workspacePath);
                }
                
                console.log('[DuilioCode Agent] Normalized path:', fullPath);
                console.log('[DuilioCode Agent] Path contains workspace?', fullPath.includes(workspacePath || ''));
                
                // FINAL SAFETY CHECK: If path still contains duplicate workspace, fix it
                if (workspacePath) {
                    const duplicatePattern = workspacePath + '/' + workspacePath;
                    if (fullPath.includes(duplicatePattern)) {
                        console.warn('[DuilioCode Agent] WARNING: Duplicate workspace detected, fixing...');
                        const escaped = workspacePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                        fullPath = fullPath.replace(new RegExp(escaped + '/' + escaped, 'g'), workspacePath);
                        console.log('[DuilioCode Agent] Fixed path:', fullPath);
                    }
                }
                
                console.log('[DuilioCode Agent] Final path to create:', fullPath);
                
                // Create the file via API
                await API.createFile(fullPath, false, content);
                
                actionsExecuted.push(`✅ Created: ${filePath}`);
                
                // Replace the code block with success message
                processedText = processedText.replace(match[0], 
                    `✅ **File created:** \`${filePath}\`\n\`\`\`\n${content.slice(0, 500)}${content.length > 500 ? '\n...(truncated)' : ''}\n\`\`\``
                );
                
            } catch (error) {
                console.error('[DuilioCode Agent] Failed to create file:', error);
                actionsExecuted.push(`❌ Failed to create: ${filePath} - ${error.message}`);
                processedText = processedText.replace(match[0], 
                    `❌ **Failed to create:** \`${filePath}\`\nError: ${error.message}`
                );
            }
        }
        
        // Process modify-file actions
        // Improved regex to handle paths with spaces and special chars
        const modifyFileRegex = /```modify-file:([^\n]+)\n([\s\S]*?)```/g;
        
        while ((match = modifyFileRegex.exec(responseText)) !== null) {
            const filePath = match[1].trim();
            const content = match[2];
            
            try {
                // CRITICAL: Normalize path to avoid duplication
                const workspacePath = AppState.workspace.currentPath;
                const fullPath = Utils.normalizeFilePath(filePath, workspacePath);
                
                console.log('[DuilioCode Agent] Modifying file:', fullPath);
                console.log('[DuilioCode Agent] Original path:', filePath);
                console.log('[DuilioCode Agent] Workspace:', workspacePath);
                
                await API.writeFile(fullPath, content);
                actionsExecuted.push(`✅ Modified: ${filePath}`);
                
                processedText = processedText.replace(match[0], 
                    `✅ **File modified:** \`${filePath}\``
                );
                
            } catch (error) {
                console.error('[DuilioCode Agent] Failed to modify file:', error);
                actionsExecuted.push(`❌ Failed to modify: ${filePath}`);
            }
        }
        
        // Process run-command actions
        const runCommandRegex = /```run-command\n([\s\S]*?)```/g;
        
        while ((match = runCommandRegex.exec(responseText)) !== null) {
            const command = match[1].trim();
            
            try {
                console.log('[DuilioCode Agent] Running command:', command);
                
                // Execute via terminal API
                const result = await API.post('/api/tools/execute', {
                    code: command,
                    language: 'shell',
                    cwd: AppState.workspace.currentPath || '~'
                });
                
                actionsExecuted.push(`✅ Executed: ${command}`);
                
                const output = result.output || result.error || 'Command completed';
                processedText = processedText.replace(match[0], 
                    `✅ **Command executed:** \`${command}\`\n\`\`\`\n${output}\n\`\`\``
                );
                
                
            } catch (error) {
                console.error('[DuilioCode Agent] Failed to run command:', error);
                actionsExecuted.push(`❌ Failed: ${command}`);
            }
        }
        
        // Show summary notification
        if (actionsExecuted.length > 0) {
            Utils.showNotification(`Agent executed ${actionsExecuted.length} action(s)`, 'success');
            
            // Refresh file tree
            if (typeof Workspace !== 'undefined') {
                Workspace.refresh();
            }
        }
        
        return processedText;
    },

    /**
     * Apply code from chat to editor
     */
    applyCode(button) {
        const pre = button.parentElement;
        const code = pre.querySelector('code').textContent;
        
        if (AppState.editor.currentFile) {
            // Use Monaco if available
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.replaceAll(code);
            } else {
                document.getElementById('codeEditor').value = code;
            }
            Utils.showNotification('Code applied to editor', 'success');
        } else {
            // Copy to clipboard
            navigator.clipboard.writeText(code);
            Utils.showNotification('Code copied to clipboard', 'success');
        }
    },
    
    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const container = document.getElementById('chatMessages');
        const indicator = document.createElement('div');
        indicator.id = 'typingIndicator';
        indicator.className = 'message';
        indicator.innerHTML = `
            <div class="message-header">
                <div class="message-avatar assistant">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                    </svg>
                </div>
                <span class="message-sender">DuilioCode</span>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        container.appendChild(indicator);
        container.scrollTop = container.scrollHeight;
    },
    
    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    },
    
    /**
     * Clear chat history
     */
    clear() {
        const container = document.getElementById('chatMessages');
        container.innerHTML = `
            <div class="message">
                <div class="message-header">
                    <div class="message-avatar assistant">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                        </svg>
                    </div>
                    <span class="message-sender">DuilioCode</span>
                </div>
                <div class="message-content">
                    <p>Hi! I'm DuilioCode, your local AI coding assistant. Ask me anything about your code, and I'll help you build, debug, or understand your projects.</p>
                </div>
            </div>
        `;
        AppState.clearMessages();
    },
    
    /**
     * Toggle chat panel size through 3 levels:
     * Normal → Expanded → Maximized → Normal
     */
    toggleSize() {
        const panel = document.getElementById('chatPanel');
        
        if (panel.classList.contains('maximized')) {
            // Maximized → Normal
            panel.classList.remove('maximized', 'expanded');
            AppState.ui.chatSize = 'normal';
        } else if (panel.classList.contains('expanded')) {
            // Expanded → Maximized
            panel.classList.remove('expanded');
            panel.classList.add('maximized');
            AppState.ui.chatSize = 'maximized';
        } else {
            // Normal → Expanded
            panel.classList.add('expanded');
            AppState.ui.chatSize = 'expanded';
        }
        
        // Update button tooltip
        const sizeBtn = document.querySelector('[data-action="toggleSize"]');
        if (sizeBtn) {
            const sizes = { normal: 'Expand', expanded: 'Maximize', maximized: 'Minimize' };
            sizeBtn.setAttribute('data-tooltip', sizes[AppState.ui.chatSize] || 'Expand');
        }
    },
    
    /**
     * Auto-resize textarea
     */
    autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    },
    
    /**
     * Handle textarea keydown
     */
    handleKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.send();
        }
    }
};
