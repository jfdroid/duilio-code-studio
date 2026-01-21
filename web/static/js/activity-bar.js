/**
 * DuilioCode Studio - Activity Bar Module
 * Manages sidebar panel switching
 */

const ActivityBar = {
    currentPanel: 'explorer',
    panels: ['explorer', 'search', 'git', 'settings'],

    /**
     * Show a specific panel
     */
    show(panelName) {
        if (!this.panels.includes(panelName)) return;

        // Hide all panels
        this.panels.forEach(name => {
            const panel = document.getElementById(`${name}Panel`);
            if (panel) panel.classList.add('hidden');
        });

        // Update activity bar buttons
        document.querySelectorAll('.activity-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected panel
        const panel = document.getElementById(`${panelName}Panel`);
        if (panel) panel.classList.remove('hidden');

        // Activate button
        const btn = document.querySelector(`.activity-btn[data-panel="${panelName}"]`);
        if (btn) btn.classList.add('active');

        // Show sidebar if hidden
        const sidebar = document.querySelector('.sidebar-panels');
        if (sidebar) sidebar.classList.remove('hidden');

        this.currentPanel = panelName;

        // Initialize panel if needed
        this.initPanel(panelName);
    },

    /**
     * Toggle current panel visibility
     */
    toggle() {
        const sidebar = document.querySelector('.sidebar-panels');
        if (sidebar) {
            sidebar.classList.toggle('hidden');
        }
    },

    /**
     * Initialize panel-specific features
     */
    initPanel(panelName) {
        switch (panelName) {
            case 'search':
                document.getElementById('searchInput')?.focus();
                break;
            case 'git':
                Git.refresh();
                break;
            case 'settings':
                Settings.init();
                break;
        }
    }
};

/**
 * Search Module
 */
const Search = {
    /**
     * Handle input
     */
    onInput(event) {
        if (event.key === 'Enter') {
            this.run();
        }
    },

    /**
     * Run search
     */
    async run() {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) return;

        const resultsContainer = document.getElementById('searchResults');
        resultsContainer.innerHTML = '<div class="search-hint">Searching...</div>';

        try {
            const caseSensitive = document.getElementById('searchCaseSensitive').checked;
            const wholeWord = document.getElementById('searchWholeWord').checked;

            // For now, search in current workspace
            if (!AppState.workspace.currentPath) {
                resultsContainer.innerHTML = '<div class="search-hint">Open a folder first to search files</div>';
                return;
            }

            const response = await fetch(`/api/files/search?path=${encodeURIComponent(AppState.workspace.currentPath)}&query=${encodeURIComponent(query)}&case_sensitive=${caseSensitive}&whole_word=${wholeWord}`);
            
            if (!response.ok) {
                throw new Error('Search failed');
            }

            const data = await response.json();
            this.renderResults(data.results || []);

        } catch (error) {
            resultsContainer.innerHTML = `<div class="search-hint">Search not yet implemented in backend</div>`;
        }
    },

    /**
     * Render search results
     */
    renderResults(results) {
        const container = document.getElementById('searchResults');

        if (results.length === 0) {
            container.innerHTML = '<div class="search-hint">No results found</div>';
            return;
        }

        container.innerHTML = results.map(r => `
            <div class="search-result-item" onclick="Files.open('${r.path}')">
                <div class="search-result-file">${r.file}</div>
                <div class="search-result-line">Line ${r.line}: ${this.escapeHtml(r.text)}</div>
            </div>
        `).join('');
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

/**
 * Git Module
 */
const Git = {
    /**
     * Refresh git status
     */
    async refresh() {
        const container = document.getElementById('gitStatus');
        
        if (!AppState.workspace.currentPath) {
            container.innerHTML = '<div class="git-hint">Open a folder to see Git status</div>';
            return;
        }

        try {
            const response = await fetch(`/api/git/status?path=${encodeURIComponent(AppState.workspace.currentPath)}`);
            
            if (!response.ok) {
                throw new Error('Not a git repository');
            }

            const data = await response.json();
            this.renderStatus(data);

        } catch (error) {
            container.innerHTML = `
                <div class="git-hint">
                    <p>Not a Git repository</p>
                    <p style="margin-top: 8px; font-size: 11px;">Initialize with: git init</p>
                </div>
            `;
        }
    },

    /**
     * Render git status
     */
    renderStatus(data) {
        const container = document.getElementById('gitStatus');

        if (!data.files || data.files.length === 0) {
            container.innerHTML = `
                <div class="git-hint">
                    <p>On branch: ${data.branch || 'main'}</p>
                    <p style="margin-top: 8px;">No changes</p>
                </div>
            `;
            return;
        }

        const statusLabels = {
            'M': { label: 'M', class: 'modified' },
            'A': { label: 'A', class: 'added' },
            'D': { label: 'D', class: 'deleted' },
            '?': { label: 'U', class: 'untracked' }
        };

        container.innerHTML = `
            <div style="padding: 8px 0; font-size: 11px; color: var(--text-muted);">
                Branch: ${data.branch || 'main'}
            </div>
            <div class="git-changes">
                ${data.files.map(f => {
                    const status = statusLabels[f.status] || { label: '?', class: 'untracked' };
                    return `
                        <div class="git-file-item" onclick="Files.open('${f.path}')">
                            <span class="git-status-badge ${status.class}">${status.label}</span>
                            <span>${f.name}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
};

/**
 * Settings Module
 */
const Settings = {
    values: {
        fontSize: 14,
        tabSize: 4,
        temperature: 0.7
    },

    /**
     * Initialize settings
     */
    init() {
        // Load from localStorage
        const saved = localStorage.getItem('duiliocode_settings');
        if (saved) {
            try {
                this.values = { ...this.values, ...JSON.parse(saved) };
            } catch (e) {}
        }

        // Update UI
        const fontSelect = document.getElementById('settingFontSize');
        if (fontSelect) fontSelect.value = this.values.fontSize;

        const tabSelect = document.getElementById('settingTabSize');
        if (tabSelect) tabSelect.value = this.values.tabSize;

        const tempSlider = document.getElementById('settingTemperature');
        if (tempSlider) {
            tempSlider.value = this.values.temperature * 100;
            document.getElementById('temperatureValue').textContent = this.values.temperature;
        }

        // Copy model selector options
        const modelSelect = document.getElementById('modelSelect');
        const settingsModelSelect = document.getElementById('settingDefaultModel');
        if (modelSelect && settingsModelSelect) {
            settingsModelSelect.innerHTML = modelSelect.innerHTML;
        }

        // Apply settings
        this.apply();
    },

    /**
     * Update a setting
     */
    update(key, value) {
        if (key === 'temperature') {
            value = value / 100;
            document.getElementById('temperatureValue').textContent = value.toFixed(1);
        }

        this.values[key] = parseInt(value) || value;
        this.save();
        this.apply();
    },

    /**
     * Save settings
     */
    save() {
        localStorage.setItem('duiliocode_settings', JSON.stringify(this.values));
    },

    /**
     * Apply settings
     */
    apply() {
        // Apply font size
        const editor = document.getElementById('codeEditor');
        if (editor) {
            editor.style.fontSize = `${this.values.fontSize}px`;
            editor.style.tabSize = this.values.tabSize;
        }
    }
};

// Global function for toggling explorer
function toggleExplorer() {
    const sidebar = document.querySelector('.sidebar-panels');
    if (sidebar) {
        if (sidebar.classList.contains('hidden')) {
            ActivityBar.show(ActivityBar.currentPanel);
        } else {
            sidebar.classList.add('hidden');
            document.querySelectorAll('.activity-btn').forEach(btn => {
                btn.classList.remove('active');
            });
        }
    }
}
