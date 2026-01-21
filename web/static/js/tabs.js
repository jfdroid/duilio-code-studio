/**
 * DuilioCode Studio - Tabs Module
 * Editor tabs management
 */

const Tabs = {
    /**
     * Add a new tab
     */
    add(path, language) {
        const name = path.split('/').pop();
        const existing = AppState.editor.openTabs.find(t => t.path === path);
        
        if (!existing) {
            AppState.addTab({ path, name, language });
        } else {
            AppState.editor.currentTab = path;
        }
        
        this.render();
        this.setActive(path);
    },
    
    /**
     * Close a tab
     */
    close(path) {
        AppState.removeTab(path);
        this.render();
        
        if (AppState.editor.currentTab === 'welcome') {
            this.showWelcome();
        } else {
            const activeTab = AppState.editor.openTabs.find(t => t.path === AppState.editor.currentTab);
            if (activeTab) {
                FileManager.open(activeTab.path);
            }
        }
    },
    
    /**
     * Set active tab
     */
    setActive(path) {
        AppState.editor.currentTab = path;
        
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.path === path || (path === 'welcome' && tab.dataset.path === 'welcome'));
        });
    },
    
    /**
     * Render tabs
     */
    render() {
        const container = document.getElementById('tabsBar');
        
        // Welcome tab
        let html = `
            <button class="tab ${AppState.editor.currentTab === 'welcome' ? 'active' : ''}" 
                    data-path="welcome" onclick="Tabs.showWelcome()">
                <span class="tab-icon">🏠</span>
                <span>Welcome</span>
            </button>
        `;
        
        // File tabs
        AppState.editor.openTabs.forEach(tab => {
            const icon = Utils.getFileIcon(tab.name);
            const isActive = AppState.editor.currentTab === tab.path;
            
            html += `
                <button class="tab ${isActive ? 'active' : ''}" data-path="${tab.path}">
                    <span class="tab-icon">${icon}</span>
                    <span>${tab.name}</span>
                    <span class="tab-close" onclick="event.stopPropagation(); Tabs.close('${tab.path}')">×</span>
                </button>
            `;
        });
        
        container.innerHTML = html;
        
        // Add click handlers
        container.querySelectorAll('.tab[data-path]:not([data-path="welcome"])').forEach(tab => {
            tab.onclick = () => FileManager.open(tab.dataset.path);
        });
    },
    
    /**
     * Show welcome screen
     */
    showWelcome() {
        AppState.editor.currentTab = 'welcome';
        AppState.setCurrentFile(null);
        
        document.getElementById('welcomeScreen').style.display = 'flex';
        document.getElementById('fileEditorContainer').style.display = 'none';
        
        this.render();
    }
};
