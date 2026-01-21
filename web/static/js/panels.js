/**
 * DuilioCode Studio - Panels Module
 * Split.js integration for resizable panels
 */

const Panels = {
    splits: {},
    
    /**
     * Initialize all splits
     */
    init() {
        if (typeof Split === 'undefined') {
            console.warn('[DuilioCode] Split.js not loaded');
            return;
        }
        
        console.log('[DuilioCode] Initializing panels...');
        
        // Initialize horizontal split (sidebar | main area | chat)
        this.initMainSplit();
    },
    
    /**
     * Initialize main horizontal split
     * Sidebar panels | Editor area | Chat panel
     */
    initMainSplit() {
        const sidebarPanels = document.querySelector('.sidebar-panels');
        const mainArea = document.querySelector('.main-area');
        const chatPanel = document.getElementById('chatPanel');
        
        if (!sidebarPanels || !mainArea || !chatPanel) {
            console.warn('[DuilioCode] Main split elements not found');
            return;
        }
        
        // Add IDs for Split.js
        sidebarPanels.id = 'sidebarPanels';
        mainArea.id = 'mainAreaSplit';
        
        // Create split
        try {
            this.splits.main = Split(['#sidebarPanels', '#mainAreaSplit', '#chatPanel'], {
                sizes: [20, 55, 25],
                minSize: [180, 300, 300],
                maxSize: [400, Infinity, 800],
                gutterSize: 4,
                cursor: 'col-resize',
                direction: 'horizontal',
                onDrag: () => this.onResize(),
                onDragEnd: () => this.onResizeEnd()
            });
            
            console.log('[DuilioCode] Main split initialized');
        } catch (error) {
            console.error('[DuilioCode] Failed to initialize main split:', error);
        }
    },
    
    /**
     * Initialize editor/terminal vertical split
     */
    initEditorTerminalSplit() {
        const editorPanel = document.getElementById('editorPanel');
        const terminalPanel = document.getElementById('terminalPanel');
        
        if (!editorPanel || !terminalPanel) return;
        
        // Don't reinitialize if already exists
        if (this.splits.editorTerminal) {
            this.splits.editorTerminal.destroy();
        }
        
        try {
            this.splits.editorTerminal = Split(['#editorPanel', '#terminalPanel'], {
                direction: 'vertical',
                sizes: [70, 30],
                minSize: [100, 100],
                gutterSize: 4,
                cursor: 'row-resize',
                onDrag: () => this.onResize(),
                onDragEnd: () => this.onResizeEnd()
            });
            
            console.log('[DuilioCode] Editor/Terminal split initialized');
        } catch (error) {
            console.error('[DuilioCode] Failed to initialize editor/terminal split:', error);
        }
    },
    
    /**
     * Destroy editor/terminal split
     */
    destroyEditorTerminalSplit() {
        if (this.splits.editorTerminal) {
            this.splits.editorTerminal.destroy();
            this.splits.editorTerminal = null;
        }
    },
    
    /**
     * Handle resize during drag
     */
    onResize() {
        // Resize Monaco editor
        if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
            MonacoEditor.resize();
        }
        
        // Resize Monaco Diff editor
        if (typeof MonacoDiff !== 'undefined' && MonacoDiff.diffEditor) {
            MonacoDiff.diffEditor.layout();
        }
        
        // Resize terminal
        if (typeof Terminal !== 'undefined' && Terminal.activeTerminal?.fitAddon) {
            Terminal.activeTerminal.fitAddon.fit();
        }
    },
    
    /**
     * Handle resize end
     */
    onResizeEnd() {
        this.onResize();
        
        // Save sizes to localStorage
        this.saveSizes();
    },
    
    /**
     * Save panel sizes
     */
    saveSizes() {
        try {
            const sizes = {};
            
            if (this.splits.main) {
                sizes.main = this.splits.main.getSizes();
            }
            
            if (this.splits.editorTerminal) {
                sizes.editorTerminal = this.splits.editorTerminal.getSizes();
            }
            
            localStorage.setItem('duilio-panel-sizes', JSON.stringify(sizes));
        } catch (e) {
            console.warn('[DuilioCode] Failed to save panel sizes');
        }
    },
    
    /**
     * Load panel sizes
     */
    loadSizes() {
        try {
            const saved = localStorage.getItem('duilio-panel-sizes');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            console.warn('[DuilioCode] Failed to load panel sizes');
        }
        return null;
    },
    
    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        const sidebar = document.getElementById('sidebarPanels');
        if (!sidebar) return;
        
        const isHidden = sidebar.style.display === 'none';
        sidebar.style.display = isHidden ? 'flex' : 'none';
        
        // Recreate split if showing
        if (isHidden && this.splits.main) {
            this.splits.main.setSizes([20, 55, 25]);
        }
        
        this.onResize();
    },
    
    /**
     * Set chat panel size
     */
    setChatSize(size) {
        if (!this.splits.main) return;
        
        const sizes = {
            'normal': [20, 55, 25],
            'expanded': [20, 45, 35],
            'maximized': [15, 35, 50]
        };
        
        if (sizes[size]) {
            this.splits.main.setSizes(sizes[size]);
            this.onResize();
        }
    }
};

// Export
window.Panels = Panels;
