/**
 * DuilioCode Studio - Application State
 * Centralized state management
 */

const AppState = {
    // Workspace state
    workspace: {
        currentPath: null,
        recentPaths: [],
        openFiles: [],
        homeDirectory: ''
    },
    
    // Editor state
    editor: {
        openTabs: [],
        currentTab: 'welcome',
        currentFile: null,
        originalContent: ''
    },
    
    // Chat state
    chat: {
        messages: [],
        isLoading: false,
        currentModel: CONFIG.DEFAULT_MODEL
    },
    
    // UI state
    ui: {
        explorerVisible: true,
        chatExpanded: false,
        contextMenuTarget: null
    },
    
    // Connection state
    connection: {
        status: 'checking',
        ollamaRunning: false
    },
    
    // Methods
    setWorkspace(data) {
        this.workspace = { ...this.workspace, ...data };
    },
    
    setCurrentFile(file) {
        this.editor.currentFile = file;
        this.editor.originalContent = file ? file.content : '';
    },
    
    addMessage(message) {
        this.chat.messages.push(message);
    },
    
    clearMessages() {
        this.chat.messages = [];
    },
    
    setLoading(loading) {
        this.chat.isLoading = loading;
    },
    
    addTab(tab) {
        const existing = this.editor.openTabs.find(t => t.path === tab.path);
        if (!existing) {
            this.editor.openTabs.push(tab);
        }
        this.editor.currentTab = tab.path;
    },
    
    removeTab(path) {
        this.editor.openTabs = this.editor.openTabs.filter(t => t.path !== path);
        if (this.editor.currentTab === path) {
            this.editor.currentTab = this.editor.openTabs.length > 0 
                ? this.editor.openTabs[this.editor.openTabs.length - 1].path 
                : 'welcome';
        }
    }
};
