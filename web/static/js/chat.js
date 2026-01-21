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
     */
    formatMessage(content) {
        // Use marked for markdown if available
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }
        
        // Basic formatting
        return content
            .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code class="language-${lang}">${Utils.escapeHtml(code.trim())}</code><button class="apply-code-btn" onclick="Chat.applyCode(this)">Apply</button></pre>`;
            })
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
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
     * Toggle chat panel size
     */
    toggleSize() {
        const panel = document.getElementById('chatPanel');
        panel.classList.toggle('expanded');
        AppState.ui.chatExpanded = panel.classList.contains('expanded');
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
