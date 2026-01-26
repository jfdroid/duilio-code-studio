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
            let errorMsg = `HTTP ${response.status}`;
            if (error.detail) {
                errorMsg = typeof error.detail === 'string' 
                    ? error.detail 
                    : (Array.isArray(error.detail) ? error.detail[0]?.msg || JSON.stringify(error.detail) : JSON.stringify(error.detail));
            }
            throw new Error(errorMsg);
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
    
    /**
     * Generate AI response with intelligent codebase context
     * @param {string} prompt - User prompt
     * @param {string|null} model - Model to use (null for auto-selection)
     * @param {string|null} context - Additional context
     */
    async generate(prompt, model, context = null) {
        // Include workspace path for codebase analysis
        const workspacePath = AppState?.workspace?.currentPath || null;
        return this.post('/api/generate', { 
            prompt, 
            model, 
            context,
            workspace_path: workspacePath,
            include_codebase: true
        });
    },
    
    /**
     * Chat with AI including intelligent codebase context
     */
    async chat(messages, model, stream = false) {
        const workspacePath = AppState?.workspace?.currentPath || null;
        return this.post('/api/chat', { 
            messages, 
            model, 
            stream,
            workspace_path: workspacePath
        });
    },
    
    /**
     * Simple chat - direct connection to Ollama/Qwen (CLEAN MODE)
     * No complex logic, just prompt → response
     */
    async chatSimple(messages, model = null, temperature = 0.7, stream = false) {
        return this.post('/api/chat/simple', {
            messages,
            model,
            temperature,
            stream
        });
    },
    
    /**
     * Analyze a codebase structure and content
     */
    async analyzeCodebase(path, maxFiles = 100) {
        return this.post('/api/analyze-codebase', { path, max_files: maxFiles });
    },
    
    /**
     * Get AI-ready codebase context
     */
    async getCodebaseContext(path, refresh = false) {
        return this.get(`/api/codebase-context?path=${encodeURIComponent(path)}&refresh=${refresh}`);
    },
    
    /**
     * Get model recommendation for a prompt
     */
    async recommendModel(prompt) {
        return this.post(`/api/recommend-model?prompt=${encodeURIComponent(prompt)}`, {});
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
