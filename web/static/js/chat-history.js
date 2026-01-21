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

        // Highlight code blocks
        container.querySelectorAll('pre code').forEach(block => {
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(block);
            }
        });
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

        document.getElementById('chatTitleText').textContent = 'New Chat';
    },

    /**
     * Format message content (markdown-like)
     */
    formatMessage(content) {
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }

        return content
            .replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code class="language-${lang}">${this.escapeHtml(code.trim())}</code><button class="apply-code-btn" onclick="Chat.applyCode(this)">Apply</button></pre>`;
            })
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
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
