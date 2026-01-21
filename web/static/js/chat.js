/**
 * DuilioCode Studio - Chat Module
 * AI assistant chat interface
 */

const Chat = {
    abortController: null,

    /**
     * Send message to AI
     */
    async send() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message || AppState.chat.isLoading) return;
        
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
            // Get file context if file is open
            let context = '';
            
            // Add workspace context
            if (AppState.workspace.currentPath) {
                context += `Current workspace: ${AppState.workspace.currentPath}\n`;
            }
            
            // Add file context
            if (AppState.editor.currentFile) {
                const content = document.getElementById('codeEditor').value;
                context += `Current file: ${AppState.editor.currentFile.path}\n\nContent:\n\`\`\`${AppState.editor.currentFile.language}\n${content.slice(0, 2000)}\n\`\`\``;
            }
            
            // Add system instruction for file operations
            const systemContext = context ? `You have access to the user's workspace. When they ask you to create files, use the workspace path as base: ${AppState.workspace.currentPath || '~'}. ${context}` : null;
            
            // Use smart model selection (pass null to let backend decide) or specific model
            const selectedModel = document.getElementById('modelSelect')?.value;
            const modelToUse = (selectedModel === 'auto' || !selectedModel) ? null : selectedModel;
            const response = await API.generate(message, modelToUse, systemContext);
            
            // Update model selector to show which model was actually used
            if (response.model && selectedModel === 'auto') {
                console.log(`[DuilioCode] Auto-selected model: ${response.model}`);
            }
            
            this.hideTypingIndicator();
            this.addMessage('assistant', response.response);
            if (typeof ChatHistory !== 'undefined') {
                ChatHistory.addMessage('assistant', response.response);
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
        
        // Highlight code blocks
        container.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
        
        AppState.addMessage({ role, content, time });
    },
    
    /**
     * Format message content (markdown-like)
     * - Makes file paths clickable
     * - Adds clickable headers to code blocks
     */
    formatMessage(content) {
        let formatted = content;
        
        // Use marked for markdown if available
        if (typeof marked !== 'undefined') {
            formatted = marked.parse(content);
        } else {
            // Basic formatting
            formatted = content
                .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                    return `<pre><code class="language-${lang}">${Utils.escapeHtml(code.trim())}</code><button class="apply-code-btn" onclick="Chat.applyCode(this)">Apply</button></pre>`;
                })
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }
        
        // Make file paths clickable
        formatted = this.makePathsClickable(formatted);
        
        // Add clickable headers to code blocks
        formatted = this.addCodeBlockHeaders(formatted);
        
        return formatted;
    },
    
    /**
     * Make file paths in text clickable
     * Detects patterns like: src/App.js, ./components/Button.tsx, etc.
     */
    makePathsClickable(html) {
        // Pattern to match file paths (not already in links)
        const pathPattern = /(?<!["'=])(\b(?:\.\/|\.\.\/|src\/|app\/|lib\/|components\/|services\/|utils\/|pages\/|api\/|tests?\/)?[\w\-./]+\.(js|jsx|ts|tsx|py|java|kt|go|rs|rb|c|cpp|h|hpp|css|scss|html|json|yaml|yml|md|txt|sh|sql))\b(?![^<]*>)/gi;
        
        return html.replace(pathPattern, (match, path) => {
            // Skip if it's a URL or already linked
            if (path.startsWith('http') || path.includes('://')) return match;
            return `<a href="#" class="file-link" onclick="Chat.openFileFromChat('${path}'); return false;" title="Open ${path}">${path}</a>`;
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
            // Create clickable header
            const header = `<div class="code-block-header" onclick="Chat.openFileFromChat('${filePath}')" title="Click to open ${filePath}">
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
        // Normalize path
        let fullPath = path;
        
        // If path doesn't start with /, prepend workspace path
        if (!path.startsWith('/') && AppState.workspace.currentPath) {
            fullPath = AppState.workspace.currentPath + '/' + path.replace(/^\.\//, '');
        }
        
        // Try to open the file
        if (typeof Files !== 'undefined' && Files.open) {
            Files.open(fullPath);
            Utils.showNotification(`Opening ${path}...`, 'info');
        } else {
            console.log('[DuilioCode] Would open file:', fullPath);
            Utils.showNotification(`File: ${path}`, 'info');
        }
    },
    
    /**
     * Apply code from chat to editor
     */
    applyCode(button) {
        const pre = button.parentElement;
        const code = pre.querySelector('code').textContent;
        
        if (AppState.editor.currentFile) {
            document.getElementById('codeEditor').value = code;
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
                    <p>Hello! I'm your local AI assistant. I can help you:</p>
                    <ul>
                        <li>Create entire projects and file structures</li>
                        <li>Edit and refactor existing code</li>
                        <li>Explain concepts and debug issues</li>
                        <li>Generate scripts, pipelines, and configs</li>
                    </ul>
                    <p>Open a folder to get started, or just ask me anything!</p>
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
