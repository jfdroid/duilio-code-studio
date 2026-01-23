/**
 * DuilioCode Studio - Quick Open
 * VS Code/Cursor style quick file open
 * 
 * Features:
 * - Cmd+P / Ctrl+P to open
 * - Fuzzy search files
 * - Recent files
 * - Symbol search (Cmd+Shift+O)
 */

const QuickOpen = {
    isVisible: false,
    files: [],
    recentFiles: [],
    selectedIndex: 0,
    filteredFiles: [],
    searchInput: null,
    container: null,
    mode: 'files', // 'files' or 'symbols'
    lastWorkspace: null,
    
    /**
     * Initialize quick open
     */
    init() {
        // Create container
        this.container = document.createElement('div');
        this.container.id = 'quickOpen';
        this.container.className = 'quick-open';
        this.container.innerHTML = `
            <div class="quick-open-overlay"></div>
            <div class="quick-open-modal">
                <div class="quick-open-header">
                    <input 
                        type="text" 
                        id="quickOpenInput" 
                        class="quick-open-input" 
                        placeholder="Type to search for files..."
                        autocomplete="off"
                        spellcheck="false"
                    />
                </div>
                <div class="quick-open-list" id="quickOpenList">
                    <!-- Files will be rendered here -->
                </div>
                <div class="quick-open-footer">
                    <span class="quick-open-hint">↑↓ Navigate • Enter Open • Esc Close</span>
                </div>
            </div>
        `;
        document.body.appendChild(this.container);
        
        // Get elements
        this.searchInput = document.getElementById('quickOpenInput');
        const overlay = this.container.querySelector('.quick-open-overlay');
        const list = document.getElementById('quickOpenList');
        
        // Event listeners
        this.searchInput.addEventListener('input', () => this.filterFiles());
        this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        overlay.addEventListener('click', () => this.hide());
        
        // Load recent files
        this.loadRecentFiles();
        
        // Don't load files here - wait for show() when workspace is ready
    },
    
    /**
     * Load files from workspace
     */
    async loadFiles() {
        if (!AppState.workspace.currentPath) {
            this.files = [];
            return;
        }
        
        try {
            // Get file tree from workspace
            const response = await API.get(`/api/files/tree?path=${encodeURIComponent(AppState.workspace.currentPath)}`);
            
            if (response.files) {
                this.files = this.flattenFiles(response.files, AppState.workspace.currentPath);
            }
        } catch (error) {
            console.error('[QuickOpen] Error loading files:', error);
            this.files = [];
        }
    },
    
    /**
     * Flatten file tree to array
     */
    flattenFiles(tree, basePath = '') {
        let files = [];
        
        for (const item of tree) {
            const fullPath = basePath ? `${basePath}/${item.name}` : item.name;
            
            if (item.type === 'file') {
                files.push({
                    name: item.name,
                    path: fullPath,
                    relativePath: fullPath.replace(AppState.workspace.currentPath + '/', '')
                });
            } else if (item.type === 'directory' && item.children) {
                files = files.concat(this.flattenFiles(item.children, fullPath));
            }
        }
        
        return files;
    },
    
    /**
     * Show quick open
     */
    async show(mode = 'files') {
        if (!this.container) {
            this.init();
        }
        
        this.mode = mode;
        this.isVisible = true;
        this.container.classList.add('visible');
        this.searchInput.value = '';
        this.selectedIndex = 0;
        
        // Update placeholder
        if (mode === 'symbols') {
            this.searchInput.placeholder = 'Type to search for symbols...';
        } else {
            this.searchInput.placeholder = 'Type to search for files...';
        }
        
        // Reload files if needed or workspace changed
        const currentWorkspace = AppState.workspace.currentPath;
        if (this.files.length === 0 || this.lastWorkspace !== currentWorkspace) {
            this.lastWorkspace = currentWorkspace;
            await this.loadFiles();
        }
        
        this.filterFiles();
        
        // Focus input after a short delay
        setTimeout(() => {
            this.searchInput.focus();
        }, 50);
    },
    
    /**
     * Hide quick open
     */
    hide() {
        this.isVisible = false;
        this.container.classList.remove('visible');
        this.searchInput.blur();
    },
    
    /**
     * Toggle quick open
     */
    toggle(mode = 'files') {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show(mode);
        }
    },
    
    /**
     * Filter files based on search
     */
    filterFiles() {
        const query = this.searchInput.value.toLowerCase().trim();
        
        if (!query) {
            // Show recent files first, then all files
            const recentPaths = new Set(this.recentFiles);
            this.filteredFiles = [
                ...this.files.filter(f => recentPaths.has(f.path)),
                ...this.files.filter(f => !recentPaths.has(f.path))
            ].slice(0, 50); // Limit to 50 results
        } else {
            // Fuzzy search
            this.filteredFiles = this.files
                .map(file => ({
                    ...file,
                    score: this.fuzzyScore(file.name.toLowerCase(), query) + 
                           this.fuzzyScore(file.relativePath.toLowerCase(), query)
                }))
                .filter(file => file.score > 0)
                .sort((a, b) => b.score - a.score)
                .slice(0, 50);
        }
        
        this.selectedIndex = 0;
        this.render();
    },
    
    /**
     * Fuzzy score algorithm
     */
    fuzzyScore(text, pattern) {
        if (!pattern) return 1;
        
        let score = 0;
        let patternIdx = 0;
        let consecutiveMatches = 0;
        
        for (let i = 0; i < text.length && patternIdx < pattern.length; i++) {
            if (text[i] === pattern[patternIdx]) {
                patternIdx++;
                consecutiveMatches++;
                // Bonus for consecutive matches
                score += consecutiveMatches * 10;
                // Bonus for matches at start of word
                if (i === 0 || text[i - 1] === '/' || text[i - 1] === '\\') {
                    score += 20;
                }
            } else {
                consecutiveMatches = 0;
            }
        }
        
        // Must match all pattern characters
        if (patternIdx !== pattern.length) {
            return 0;
        }
        
        return score;
    },
    
    /**
     * Render file list
     */
    render() {
        const list = document.getElementById('quickOpenList');
        
        if (this.filteredFiles.length === 0) {
            list.innerHTML = '<div class="quick-open-empty">No files found</div>';
            return;
        }
        
        let html = '';
        
        this.filteredFiles.forEach((file, index) => {
            const isSelected = index === this.selectedIndex;
            const isRecent = this.recentFiles.includes(file.path);
            
            html += `
                <div class="quick-open-item ${isSelected ? 'selected' : ''} ${isRecent ? 'recent' : ''}" data-index="${index}">
                    <span class="quick-open-icon">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                    </span>
                    <span class="quick-open-label">${this.highlightMatch(file.name, this.searchInput.value)}</span>
                    <span class="quick-open-path">${file.relativePath}</span>
                </div>
            `;
        });
        
        list.innerHTML = html;
        
        // Scroll selected into view
        const selected = list.querySelector('.quick-open-item.selected');
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
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredFiles.length - 1);
                this.render();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.render();
                break;
                
            case 'Enter':
                event.preventDefault();
                this.openSelected();
                break;
        }
    },
    
    /**
     * Open selected file
     */
    openSelected() {
        if (this.filteredFiles.length === 0) return;
        
        const file = this.filteredFiles[this.selectedIndex];
        if (!file) return;
        
        // Add to recent
        this.addToRecent(file.path);
        
        // Hide quick open
        this.hide();
        
        // Open file
        if (typeof FileManager !== 'undefined' && FileManager.open) {
            FileManager.open(file.path);
        }
    },
    
    /**
     * Add file to recent
     */
    addToRecent(filePath) {
        // Remove if already exists
        this.recentFiles = this.recentFiles.filter(path => path !== filePath);
        
        // Add to beginning
        this.recentFiles.unshift(filePath);
        
        // Keep only last 20
        if (this.recentFiles.length > 20) {
            this.recentFiles = this.recentFiles.slice(0, 20);
        }
        
        // Save to localStorage
        try {
            localStorage.setItem('duilio-quick-open-recent', JSON.stringify(this.recentFiles));
        } catch (e) {
            console.warn('[QuickOpen] Failed to save recent files');
        }
    },
    
    /**
     * Load recent files
     */
    loadRecentFiles() {
        try {
            const saved = localStorage.getItem('duilio-quick-open-recent');
            if (saved) {
                this.recentFiles = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('[QuickOpen] Failed to load recent files');
        }
    }
};

// Export
window.QuickOpen = QuickOpen;
