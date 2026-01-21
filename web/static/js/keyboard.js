/**
 * DuilioCode Studio - Keyboard Shortcuts Module
 * Global keyboard shortcut handling
 */

const Keyboard = {
    /**
     * Initialize keyboard shortcuts
     */
    init() {
        document.addEventListener('keydown', this.handleGlobalKeydown.bind(this));
    },
    
    /**
     * Handle global keydown
     */
    handleGlobalKeydown(event) {
        const ctrlOrMeta = event.ctrlKey || event.metaKey;
        
        // Save: Ctrl+S
        if (ctrlOrMeta && event.key === 's') {
            event.preventDefault();
            FileManager.save();
            return;
        }
        
        // Open Folder: Ctrl+O
        if (ctrlOrMeta && event.key === 'o') {
            event.preventDefault();
            Workspace.openModal();
            return;
        }
        
        // New File: Ctrl+N
        if (ctrlOrMeta && event.key === 'n') {
            event.preventDefault();
            FileManager.createNew();
            return;
        }
        
        // Toggle Explorer: Ctrl+B
        if (ctrlOrMeta && event.key === 'b') {
            event.preventDefault();
            UI.toggleExplorer();
            return;
        }
        
        // Escape: Close modals
        if (event.key === 'Escape') {
            Workspace.closeModal();
            FileManager.closeModal();
            ContextMenu.hide();
            return;
        }
    }
};
