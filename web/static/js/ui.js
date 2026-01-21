/**
 * DuilioCode Studio - UI Module
 * UI state and interactions
 */

const UI = {
    /**
     * Toggle explorer panel visibility
     */
    toggleExplorer() {
        const panel = document.getElementById('explorerPanel');
        panel.classList.toggle('hidden');
        AppState.ui.explorerVisible = !panel.classList.contains('hidden');
        
        // Update activity button
        const btn = document.querySelector('.activity-btn[data-panel="explorer"]');
        if (btn) {
            btn.classList.toggle('active', AppState.ui.explorerVisible);
        }
    },
    
    /**
     * Update connection status
     */
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connectionStatus');
        const statusDot = document.getElementById('statusDot');
        const modelStatus = document.getElementById('modelStatus');
        
        if (status.status === 'ok' && status.ollama?.status === 'running') {
            indicator.textContent = 'Connected';
            statusDot.className = 'status-dot';
            
            if (status.ollama?.models_count > 0) {
                modelStatus.textContent = `${status.ollama.models_count} models`;
            }
            
            AppState.connection.status = 'connected';
            AppState.connection.ollamaRunning = true;
        } else {
            indicator.textContent = 'Offline';
            statusDot.className = 'status-dot offline';
            AppState.connection.status = 'offline';
            AppState.connection.ollamaRunning = false;
        }
    },
    
    /**
     * Check connection
     */
    async checkConnection() {
        try {
            const status = await API.checkHealth();
            this.updateConnectionStatus(status);
        } catch (error) {
            this.updateConnectionStatus({ status: 'error' });
        }
    },
    
    /**
     * Load available models
     */
    async loadModels() {
        try {
            const data = await API.listModels();
            const select = document.getElementById('modelSelect');
            
            if (select && data.models) {
                select.innerHTML = data.models.map(m => 
                    `<option value="${m.name}" ${m.name === CONFIG.DEFAULT_MODEL ? 'selected' : ''}>${m.name}</option>`
                ).join('');
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    },
    
    /**
     * Set model
     */
    setModel(model) {
        AppState.chat.currentModel = model;
    },
    
    /**
     * Quick prompt
     */
    quickPrompt(prompt) {
        document.getElementById('chatInput').value = prompt;
        Chat.send();
    }
};
