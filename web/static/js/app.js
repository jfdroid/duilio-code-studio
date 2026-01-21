/**
 * DuilioCode Studio - Main Application Entry Point
 * 
 * This file initializes all modules and sets up the application.
 * Load this file last after all other modules.
 */

const App = {
    /**
     * Initialize the application
     */
    async init() {
        console.log('[DuilioCode] Initializing...');
        
        try {
            // Initialize keyboard shortcuts
            Keyboard.init();
            
            // Initialize Monaco Editor (async, non-blocking)
            if (typeof MonacoEditor !== 'undefined') {
                MonacoEditor.init().then(() => {
                    console.log('[DuilioCode] Monaco Editor ready');
                    // Initialize Monaco Diff after Monaco is ready
                    if (typeof MonacoDiff !== 'undefined') {
                        MonacoDiff.init();
                    }
                }).catch(err => {
                    console.warn('[DuilioCode] Monaco failed to load, using fallback editor:', err);
                });
            }
            
            // Initialize Terminal
            if (typeof Terminal !== 'undefined') {
                Terminal.init();
            }
            
            // Initialize Chat Renderers (Mermaid, KaTeX)
            if (typeof ChatRenderers !== 'undefined') {
                ChatRenderers.init();
            }
            
            // Load workspace
            await Workspace.init();
            
            // Load models
            await UI.loadModels();
            
            // Check connection
            await UI.checkConnection();
            
            // Set up connection check interval
            setInterval(() => UI.checkConnection(), CONFIG.CONNECTION_CHECK_INTERVAL);
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Render initial tabs
            Tabs.render();
            
            // Initialize chat history
            if (typeof ChatHistory !== 'undefined') {
                ChatHistory.init();
            }
            
            console.log('[DuilioCode] Ready');
            
        } catch (error) {
            console.error('[DuilioCode] Initialization error:', error);
        }
    },
    
    /**
     * Set up global event listeners
     */
    setupEventListeners() {
        // Context menu
        document.addEventListener('contextmenu', (e) => ContextMenu.show(e));
        document.addEventListener('click', () => ContextMenu.hide());
        
        // Chat textarea auto-resize
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('input', () => Chat.autoResize(chatInput));
            chatInput.addEventListener('keydown', (e) => Chat.handleKeydown(e));
        }
        
        // Model selector
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.addEventListener('change', (e) => UI.setModel(e.target.value));
        }
        
        // Window resize - update Monaco layout
        window.addEventListener('resize', () => {
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.resize();
            }
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());


// ============================================
// GLOBAL FUNCTIONS (for HTML onclick handlers)
// ============================================

// Workspace
function openWorkspaceModal() { Workspace.openModal(); }
function closeWorkspaceModal() { Workspace.closeModal(); }
function openWorkspace() { Workspace.open(); }

// Path Autocomplete
function handlePathInput(value) { PathAutocomplete.handleInput(value); }
function handlePathKeydown(event) { PathAutocomplete.handleKeydown(event); }
function setQuickPath(path) { PathAutocomplete.setQuickPath(path); }

// Files
function createNewFile() { FileManager.createNew(); }
function createNewFolder() { FileManager.createNewFolder(); }
function saveCurrentFile() { FileManager.save(); }
function revertFile() { FileManager.revert(); }
function closeNewFileModal() { FileManager.closeModal(); }
function confirmCreateFile() { FileManager.confirmCreate(); }

// Chat
function sendMessage() { Chat.send(); }
function clearChat() { Chat.clear(); }
function toggleChatSize() { Chat.toggleSize(); }
function quickPrompt(prompt) { UI.quickPrompt(prompt); }

// Context Menu
function contextNewFile() { ContextMenu.newFile(); }
function contextNewFolder() { ContextMenu.newFolder(); }
function contextRename() { ContextMenu.rename(); }
function contextCopyPath() { ContextMenu.copyPath(); }
function contextDelete() { ContextMenu.delete(); }

// UI
function toggleExplorer() { UI.toggleExplorer(); }
function toggleChatHistory() { 
    const sidebar = document.getElementById('chatHistorySidebar');
    if (sidebar) sidebar.classList.toggle('visible');
}
function openSearch() { ActivityBar.show('search'); }
function focusChat() { document.getElementById('chatInput')?.focus(); }
function toggleTerminal() { 
    if (typeof Terminal !== 'undefined') {
        Terminal.toggle(); 
    }
}
