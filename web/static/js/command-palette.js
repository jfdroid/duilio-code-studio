/**
 * DuilioCode Studio - Command Palette
 * VS Code/Cursor style command palette
 * 
 * Features:
 * - Cmd+Shift+P / Ctrl+Shift+P to open
 * - Fuzzy search commands
 * - Categories
 * - Keyboard shortcuts display
 * - Recent commands
 */

const CommandPalette = {
    isVisible: false,
    commands: [],
    recentCommands: [],
    selectedIndex: 0,
    filteredCommands: [],
    searchInput: null,
    container: null,
    
    /**
     * Initialize command palette
     */
    init() {
        // Create container
        this.container = document.createElement('div');
        this.container.id = 'commandPalette';
        this.container.className = 'command-palette';
        this.container.innerHTML = `
            <div class="command-palette-overlay"></div>
            <div class="command-palette-modal">
                <div class="command-palette-header">
                    <input 
                        type="text" 
                        id="commandPaletteInput" 
                        class="command-palette-input" 
                        placeholder="Type a command name..."
                        autocomplete="off"
                        spellcheck="false"
                    />
                </div>
                <div class="command-palette-list" id="commandPaletteList">
                    <!-- Commands will be rendered here -->
                </div>
                <div class="command-palette-footer">
                    <span class="command-palette-hint">↑↓ Navigate • Enter Select • Esc Close</span>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);
        
        // Get elements
        this.searchInput = document.getElementById('commandPaletteInput');
        const overlay = this.container.querySelector('.command-palette-overlay');
        const list = document.getElementById('commandPaletteList');
        
        // Register commands
        this.registerCommands();
        
        // Event listeners
        this.searchInput.addEventListener('input', () => this.filterCommands());
        this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        overlay.addEventListener('click', () => this.hide());
        
        // Load recent commands
        this.loadRecentCommands();
    },
    
    /**
     * Register all available commands
     */
    registerCommands() {
        this.commands = [
            // File Operations
            {
                id: 'file.new',
                label: 'New File',
                category: 'File',
                action: () => FileManager.createNew()
            },
            {
                id: 'file.newFolder',
                label: 'New Folder',
                category: 'File',
                action: () => FileManager.createNewFolder()
            },
            {
                id: 'file.save',
                label: 'Save',
                category: 'File',
                action: () => FileManager.save()
            },
            {
                id: 'file.open',
                label: 'Open Folder...',
                category: 'File',
                action: () => Workspace.openModal()
            },
            
            // Workspace
            {
                id: 'workspace.refresh',
                label: 'Refresh Explorer',
                category: 'Workspace',
                action: () => Workspace.refresh()
            },
            
            // View
            {
                id: 'view.toggleExplorer',
                label: 'Toggle Explorer',
                category: 'View',
                action: () => UI.toggleExplorer()
            },
            {
                id: 'view.toggleChat',
                label: 'Toggle Chat',
                category: 'View',
                action: () => Chat.toggleSize()
            },
            
            // Editor
            {
                id: 'editor.format',
                label: 'Format Document',
                category: 'Editor',
                action: () => {
                    if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                        MonacoEditor.format();
                    }
                }
            },
            
            // Chat
            {
                id: 'chat.clear',
                label: 'Clear Chat',
                category: 'Chat',
                action: () => Chat.clear()
            },
            {
                id: 'chat.focus',
                label: 'Focus Chat',
                category: 'Chat',
                action: () => {
                    const input = document.getElementById('chatInput');
                    if (input) input.focus();
                }
            },
            
            // Settings
            {
                id: 'settings.open',
                label: 'Open Settings',
                category: 'Settings',
                action: () => ActivityBar.show('settings')
            }
        ];
        
        // Sort by category and label
        this.commands.sort((a, b) => {
            if (a.category !== b.category) {
                return a.category.localeCompare(b.category);
            }
            return a.label.localeCompare(b.label);
        });
    },
    
    /**
     * Show command palette
     */
    show() {
        if (!this.container) {
            this.init();
        }
        
        this.isVisible = true;
        this.container.classList.add('visible');
        this.searchInput.value = '';
        this.selectedIndex = 0;
        this.filteredCommands = [...this.commands];
        this.render();
        
        // Focus input after a short delay
        setTimeout(() => {
            this.searchInput.focus();
        }, 50);
    },
    
    /**
     * Hide command palette
     */
    hide() {
        this.isVisible = false;
        this.container.classList.remove('visible');
        this.searchInput.blur();
    },
    
    /**
     * Toggle command palette
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    },
    
    /**
     * Filter commands based on search
     */
    filterCommands() {
        const query = this.searchInput.value.toLowerCase().trim();
        
        if (!query) {
            this.filteredCommands = [...this.commands];
        } else {
            // Simple fuzzy search
            this.filteredCommands = this.commands.filter(cmd => {
                const searchText = `${cmd.category} ${cmd.label} ${cmd.shortcut || ''}`.toLowerCase();
                return searchText.includes(query) || 
                       this.fuzzyMatch(cmd.label.toLowerCase(), query) ||
                       this.fuzzyMatch(cmd.category.toLowerCase(), query);
            });
        }
        
        this.selectedIndex = 0;
        this.render();
    },
    
    /**
     * Simple fuzzy match
     */
    fuzzyMatch(text, pattern) {
        let patternIdx = 0;
        for (let i = 0; i < text.length && patternIdx < pattern.length; i++) {
            if (text[i] === pattern[patternIdx]) {
                patternIdx++;
            }
        }
        return patternIdx === pattern.length;
    },
    
    /**
     * Render command list
     */
    render() {
        const list = document.getElementById('commandPaletteList');
        
        if (this.filteredCommands.length === 0) {
            list.innerHTML = '<div class="command-palette-empty">No commands found</div>';
            return;
        }
        
        let html = '';
        let currentCategory = '';
        
        this.filteredCommands.forEach((cmd, index) => {
            // Category header
            if (cmd.category !== currentCategory) {
                currentCategory = cmd.category;
                html += `<div class="command-palette-category">${currentCategory}</div>`;
            }
            
            // Command item
            const isSelected = index === this.selectedIndex;
            html += `
                <div class="command-palette-item ${isSelected ? 'selected' : ''}" data-index="${index}">
                    <span class="command-palette-label">${this.highlightMatch(cmd.label, this.searchInput.value)}</span>
                </div>
            `;
        });
        
        list.innerHTML = html;
        
        // Scroll selected into view
        const selected = list.querySelector('.command-palette-item.selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    },
    
    /**
     * Highlight matching text
     */
    highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    },
    
    /**
     * Handle keyboard input
     */
    handleKeydown(event) {
        switch (event.key) {
            case 'Escape':
                event.preventDefault();
                this.hide();
                break;
                
            case 'ArrowDown':
                event.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredCommands.length - 1);
                this.render();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.render();
                break;
                
            case 'Enter':
                event.preventDefault();
                this.executeSelected();
                break;
        }
    },
    
    /**
     * Execute selected command
     */
    executeSelected() {
        if (this.filteredCommands.length === 0) return;
        
        const command = this.filteredCommands[this.selectedIndex];
        if (!command) return;
        
        // Add to recent
        this.addToRecent(command.id);
        
        // Hide palette
        this.hide();
        
        // Execute command
        try {
            command.action();
        } catch (error) {
            console.error('[CommandPalette] Error executing command:', error);
            if (typeof Utils !== 'undefined') {
                Utils.showNotification(`Error: ${error.message}`, 'error');
            }
        }
    },
    
    /**
     * Add command to recent
     */
    addToRecent(commandId) {
        // Remove if already exists
        this.recentCommands = this.recentCommands.filter(id => id !== commandId);
        
        // Add to beginning
        this.recentCommands.unshift(commandId);
        
        // Keep only last 10
        if (this.recentCommands.length > 10) {
            this.recentCommands = this.recentCommands.slice(0, 10);
        }
        
        // Save to localStorage
        try {
            localStorage.setItem('duilio-command-palette-recent', JSON.stringify(this.recentCommands));
        } catch (e) {
            console.warn('[CommandPalette] Failed to save recent commands');
        }
    },
    
    /**
     * Load recent commands
     */
    loadRecentCommands() {
        try {
            const saved = localStorage.getItem('duilio-command-palette-recent');
            if (saved) {
                this.recentCommands = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('[CommandPalette] Failed to load recent commands');
        }
    }
};

// Export
window.CommandPalette = CommandPalette;
