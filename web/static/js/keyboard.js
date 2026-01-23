/**
 * DuilioCode Studio - Keyboard Shortcuts Module
 * Minimal keyboard handling - only Escape for closing modals
 * 
 * NOTE: We removed most keyboard shortcuts to avoid conflicts with browser shortcuts.
 * Users can access features via UI buttons and Command Palette.
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
        // Only handle Escape for closing modals/palettes
        // This doesn't conflict with browser shortcuts
        if (event.key === 'Escape') {
            // Close command palette first
            if (typeof CommandPalette !== 'undefined' && CommandPalette.isVisible) {
                event.preventDefault();
                CommandPalette.hide();
                return;
            }
            // Close quick open
            if (typeof QuickOpen !== 'undefined' && QuickOpen.isVisible) {
                event.preventDefault();
                QuickOpen.hide();
                return;
            }
            // Close other modals
            Workspace.closeModal();
            FileManager.closeModal();
            ContextMenu.hide();
            return;
        }
    }
};
