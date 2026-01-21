/**
 * DuilioCode Studio - Path Autocomplete Module
 * Directory path autocomplete for Open Folder dialog
 */

const PathAutocomplete = {
    suggestions: [],
    selectedIndex: -1,
    timeout: null,
    
    /**
     * Handle input change
     */
    async handleInput(value) {
        clearTimeout(this.timeout);
        
        if (!value || value.length < 1) {
            this.hide();
            return;
        }
        
        // Debounce
        this.timeout = setTimeout(async () => {
            await this.fetch(value);
        }, 150);
    },
    
    /**
     * Fetch suggestions from API
     */
    async fetch(partial) {
        try {
            const data = await API.autocomplete(partial);
            this.suggestions = data.suggestions || [];
            this.selectedIndex = -1;
            this.render();
        } catch (error) {
            console.error('Autocomplete error:', error);
            this.hide();
        }
    },
    
    /**
     * Render suggestions
     */
    render() {
        const container = document.getElementById('pathSuggestions');
        
        if (this.suggestions.length === 0) {
            this.hide();
            return;
        }
        
        container.innerHTML = this.suggestions.map((item, index) => `
            <div class="path-suggestion ${index === this.selectedIndex ? 'selected' : ''}"
                 onclick="PathAutocomplete.select(${index})"
                 onmouseenter="PathAutocomplete.highlight(${index})">
                <span class="path-suggestion-icon">📁</span>
                <span class="path-suggestion-text">
                    <span class="path-suggestion-name">${item.name}</span>
                    <span style="color: var(--text-muted); margin-left: 8px;">${item.path}</span>
                </span>
            </div>
        `).join('');
        
        container.classList.add('active');
    },
    
    /**
     * Hide suggestions
     */
    hide() {
        const container = document.getElementById('pathSuggestions');
        if (container) {
            container.classList.remove('active');
        }
        this.suggestions = [];
        this.selectedIndex = -1;
    },
    
    /**
     * Highlight suggestion
     */
    highlight(index) {
        this.selectedIndex = index;
        document.querySelectorAll('.path-suggestion').forEach((item, idx) => {
            item.classList.toggle('selected', idx === index);
        });
    },
    
    /**
     * Select suggestion
     */
    select(index) {
        if (index >= 0 && index < this.suggestions.length) {
            const suggestion = this.suggestions[index];
            const input = document.getElementById('workspaceInput');
            input.value = suggestion.path + '/';
            this.hide();
            input.focus();
            // Trigger another fetch for subdirectories
            this.handleInput(input.value);
        }
    },
    
    /**
     * Handle keyboard navigation
     */
    handleKeydown(event) {
        const container = document.getElementById('pathSuggestions');
        const isVisible = container && container.classList.contains('active');
        
        if (!isVisible) {
            if (event.key === 'Enter') {
                Workspace.open();
            }
            return;
        }
        
        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
                this.highlight(this.selectedIndex);
                this.scrollIntoView();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.highlight(this.selectedIndex);
                this.scrollIntoView();
                break;
                
            case 'Tab':
            case 'Enter':
                event.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.select(this.selectedIndex);
                } else if (this.suggestions.length > 0) {
                    this.select(0);
                } else if (event.key === 'Enter') {
                    Workspace.open();
                }
                break;
                
            case 'Escape':
                this.hide();
                break;
        }
    },
    
    /**
     * Scroll selected into view
     */
    scrollIntoView() {
        const selected = document.querySelector('.path-suggestion.selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest' });
        }
    },
    
    /**
     * Set quick path
     */
    setQuickPath(path) {
        const input = document.getElementById('workspaceInput');
        input.value = path + '/';
        input.focus();
        this.handleInput(input.value);
    }
};
