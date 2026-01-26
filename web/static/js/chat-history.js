/**
 * DuilioCode Studio - Chat History Module
 * Manages multiple chat conversations
 */

const ChatHistory = {
    chats: [],
    currentChatId: null,
    abortController: null,

    /**
     * Initialize chat history
     */
    init() {
        // Load from localStorage
        const saved = localStorage.getItem('duiliocode_chats');
        if (saved) {
            try {
                this.chats = JSON.parse(saved);
            } catch (e) {
                this.chats = [];
            }
        }

        // Create default chat if none exist
        if (this.chats.length === 0) {
            this.create();
        } else {
            // Load most recent chat
            this.load(this.chats[0].id);
        }

        this.render();
    },

    /**
     * Create a new chat
     */
    create() {
        const id = Date.now().toString();
        const chat = {
            id,
            title: 'New Chat',
            messages: [],
            createdAt: new Date().toISOString()
        };

        this.chats.unshift(chat);
        this.currentChatId = id;
        this.save();
        this.render();
        this.clearMessages();

        return chat;
    },

    /**
     * Load a chat by ID
     */
    load(chatId) {
        const chat = this.chats.find(c => c.id === chatId);
        if (!chat) return;

        this.currentChatId = chatId;
        this.render();
        this.renderMessages(chat.messages);

        // Update title in header
        document.getElementById('chatTitleText').textContent = chat.title || 'New Chat';
    },

    /**
     * Delete a chat by ID
     */
    delete(chatId) {
        const index = this.chats.findIndex(c => c.id === chatId);
        if (index === -1) return;

        this.chats.splice(index, 1);

        // If deleted current chat, load another or create new
        if (chatId === this.currentChatId) {
            if (this.chats.length > 0) {
                this.load(this.chats[0].id);
            } else {
                this.create();
            }
        }

        this.save();
        this.render();
    },

    /**
     * Add message to current chat
     */
    addMessage(role, content) {
        const chat = this.getCurrentChat();
        if (!chat) return;

        chat.messages.push({
            role,
            content,
            timestamp: new Date().toISOString()
        });

        // Update title from first user message
        if (role === 'user' && chat.title === 'New Chat') {
            chat.title = content.slice(0, 40) + (content.length > 40 ? '...' : '');
            document.getElementById('chatTitleText').textContent = chat.title;
        }

        this.save();
        this.render();
    },

    /**
     * Get current chat
     */
    getCurrentChat() {
        return this.chats.find(c => c.id === this.currentChatId);
    },

    /**
     * Save to localStorage
     */
    save() {
        localStorage.setItem('duiliocode_chats', JSON.stringify(this.chats));
    },

    /**
     * Render chat history list
     */
    render() {
        const container = document.getElementById('chatHistoryList');
        if (!container) return;

        container.innerHTML = this.chats.map(chat => `
            <div class="chat-history-item ${chat.id === this.currentChatId ? 'active' : ''}"
                 onclick="ChatHistory.load('${chat.id}')">
                <span class="chat-history-item-title">${this.escapeHtml(chat.title)}</span>
                <span class="chat-history-item-delete" onclick="event.stopPropagation(); ChatHistory.delete('${chat.id}')" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </span>
            </div>
        `).join('');
    },

    /**
     * Render messages for a chat
     */
    renderMessages(messages) {
        const container = document.getElementById('chatMessages');
        if (!container) return;

        if (messages.length === 0) {
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
            return;
        }

        container.innerHTML = messages.map(msg => {
            const avatarContent = msg.role === 'user' 
                ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';

            return `
                <div class="message">
                    <div class="message-header">
                        <div class="message-avatar ${msg.role}">${avatarContent}</div>
                        <span class="message-sender">${msg.role === 'user' ? 'You' : 'DuilioCode'}</span>
                    </div>
                    <div class="message-content">${this.formatMessage(msg.content)}</div>
                </div>
            `;
        }).join('');

        container.scrollTop = container.scrollHeight;
        
        // Attach event listeners to file links (using data attributes)
        container.querySelectorAll('.file-link[data-file-path]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const filePath = link.getAttribute('data-file-path');
                if (filePath && typeof Chat !== 'undefined' && Chat.openFileFromChat) {
                    Chat.openFileFromChat(filePath);
                }
            });
        });
        
        // Code block headers
        container.querySelectorAll('.code-block-header[data-file-path]').forEach(header => {
            header.addEventListener('click', (e) => {
                e.preventDefault();
                const filePath = header.getAttribute('data-file-path');
                if (filePath && typeof Chat !== 'undefined' && Chat.openFileFromChat) {
                    Chat.openFileFromChat(filePath);
                }
            });
            header.style.cursor = 'pointer';
        });

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
                    console.debug('[ChatHistory] Highlight error:', error);
                }
            });
        }
    },

    /**
     * Clear messages in UI
     */
    clearMessages() {
        const container = document.getElementById('chatMessages');
        if (!container) return;

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

        document.getElementById('chatTitleText').textContent = 'New Chat';
    },

    /**
     * Format message content (markdown-like)
     */
    formatMessage(content) {
        let formatted = content;
        
        if (typeof marked !== 'undefined') {
            formatted = marked.parse(content);
        } else {
            formatted = content
                .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                    return `<pre><code class="language-${lang}">${this.escapeHtml(code.trim())}</code><button class="apply-code-btn" onclick="Chat.applyCode(this)">Apply</button></pre>`;
                })
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }
        
        // Make file paths clickable (same as Chat.formatMessage)
        if (typeof Chat !== 'undefined' && Chat.makePathsClickable) {
            formatted = Chat.makePathsClickable(formatted);
        }
        
        // Add clickable headers to code blocks
        if (typeof Chat !== 'undefined' && Chat.addCodeBlockHeaders) {
            formatted = Chat.addCodeBlockHeaders(formatted);
        }
        
        return formatted;
    },

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

/**
 * Toggle chat history sidebar
 */
function toggleChatHistory() {
    const sidebar = document.getElementById('chatHistorySidebar');
    sidebar.classList.toggle('visible');
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    ChatHistory.init();
});
