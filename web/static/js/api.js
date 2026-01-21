/**
 * DuilioCode Studio - API Client
 * HTTP communication with backend
 */

const API = {
    /**
     * Make a GET request
     */
    async get(endpoint) {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    },
    
    /**
     * Make a POST request
     */
    async post(endpoint, data) {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    },
    
    // === Workspace ===
    
    async getWorkspace() {
        return this.get('/api/workspace');
    },
    
    async setWorkspace(path) {
        return this.post('/api/workspace', { path });
    },
    
    async getWorkspaceTree(path, depth = 3) {
        return this.get(`/api/workspace/tree?path=${encodeURIComponent(path)}&depth=${depth}`);
    },
    
    // === Files ===
    
    async readFile(path) {
        return this.get(`/api/files/read?path=${encodeURIComponent(path)}`);
    },
    
    async writeFile(path, content) {
        return this.post('/api/files/write', { path, content });
    },
    
    async createFile(path, isDirectory = false, content = '') {
        return this.post('/api/files/create', { path, is_directory: isDirectory, content });
    },
    
    async deleteFile(path) {
        return this.post('/api/files/delete', { path });
    },
    
    async listDirectory(path, showHidden = false) {
        return this.get(`/api/files/list?path=${encodeURIComponent(path)}&show_hidden=${showHidden}`);
    },
    
    async autocomplete(partial) {
        return this.get(`/api/files/autocomplete?partial=${encodeURIComponent(partial)}`);
    },
    
    // === Chat / AI ===
    
    async generate(prompt, model, context = null) {
        return this.post('/api/generate', { prompt, model, context });
    },
    
    async chat(messages, model, stream = false) {
        return this.post('/api/chat', { messages, model, stream });
    },
    
    // === Models ===
    
    async listModels() {
        return this.get('/api/models');
    },
    
    // === Health ===
    
    async checkHealth() {
        return this.get('/health/full');
    }
};
