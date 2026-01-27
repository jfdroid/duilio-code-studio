/**
 * DuilioCode Studio - Panels Module
 * Resizable panels with CSS resize + manual drag
 */

const Panels = {
    isDragging: false,
    currentResizer: null,
    startX: 0,
    startY: 0,
    startWidth: 0,
    startHeight: 0,
    
    /**
     * Initialize panels
     */
    init() {
        console.log('[DuilioCode] Initializing panels...');
        
        // Create resizers
        this.createResizers();
        
        // Load saved sizes
        this.loadSizes();
    },
    
    /**
     * Create drag resizers between panels
     */
    createResizers() {
        // Resizer between sidebar and main area
        const sidebar = document.querySelector('.sidebar-panels');
        const mainArea = document.querySelector('.main-area');
        
        if (sidebar && mainArea) {
            const resizerLeft = document.createElement('div');
            resizerLeft.className = 'panel-resizer panel-resizer-vertical';
            resizerLeft.dataset.target = 'sidebar';
            sidebar.after(resizerLeft);
            
            this.setupResizer(resizerLeft, sidebar, 'width');
        }
        
        // Resizer between main area and chat (chat is now sibling of main-area)
        const mainAreaContainer = document.querySelector('.main-area');
        const chatPanel = document.getElementById('chatPanel');
        if (mainAreaContainer && chatPanel) {
            const resizerRight = document.createElement('div');
            resizerRight.className = 'panel-resizer panel-resizer-vertical';
            resizerRight.dataset.target = 'chat';
            mainAreaContainer.after(resizerRight);
            
            this.setupResizer(resizerRight, chatPanel, 'width', true);
        }
    },
    
    /**
     * Setup a resizer element
     */
    setupResizer(resizer, target, dimension, inverse = false) {
        resizer.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDragging = true;
            this.currentResizer = resizer;
            this.startX = e.clientX;
            this.startY = e.clientY;
            
            if (dimension === 'width') {
                this.startWidth = target.offsetWidth;
            } else {
                this.startHeight = target.offsetHeight;
            }
            
            resizer.classList.add('active');
            document.body.style.cursor = dimension === 'width' ? 'col-resize' : 'row-resize';
            document.body.style.userSelect = 'none';
            
            const onMouseMove = (e) => {
                if (!this.isDragging) return;
                
                if (dimension === 'width') {
                    const delta = inverse ? (this.startX - e.clientX) : (e.clientX - this.startX);
                    const newWidth = Math.max(200, Math.min(600, this.startWidth + delta));
                    target.style.width = newWidth + 'px';
                    target.style.flex = 'none';
                } else {
                    const delta = inverse ? (this.startY - e.clientY) : (e.clientY - this.startY);
                    const newHeight = Math.max(100, Math.min(500, this.startHeight + delta));
                    target.style.height = newHeight + 'px';
                }
                
                this.onResize();
            };
            
            const onMouseUp = () => {
                this.isDragging = false;
                resizer.classList.remove('active');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                
                this.saveSizes();
            };
            
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    },
    
    /**
     * Handle resize - update Monaco and Terminal
     */
    onResize() {
        // Resize Monaco editor
        if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
            MonacoEditor.resize();
        }
    },
    
    /**
     * Save panel sizes
     */
    saveSizes() {
        try {
            const sidebar = document.querySelector('.sidebar-panels');
            const chatPanel = document.getElementById('chatPanel');
            
            const sizes = {
                sidebar: sidebar?.offsetWidth || 260,
                chat: chatPanel?.offsetWidth || 380
            };
            
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
                const sizes = JSON.parse(saved);
                
                const sidebar = document.querySelector('.sidebar-panels');
                const chatPanel = document.getElementById('chatPanel');
                
                if (sidebar && sizes.sidebar) {
                    sidebar.style.width = sizes.sidebar + 'px';
                    sidebar.style.flex = 'none';
                }
                
                if (chatPanel && sizes.chat) {
                    chatPanel.style.width = sizes.chat + 'px';
                    chatPanel.style.flex = 'none';
                }
            }
        } catch (e) {
            console.warn('[DuilioCode] Failed to load panel sizes');
        }
    },
    
    /**
     * Set chat panel size preset
     */
    setChatSize(size) {
        const chatPanel = document.getElementById('chatPanel');
        if (!chatPanel) return;
        
        const sizes = {
            'normal': 380,
            'expanded': 500,
            'maximized': 700
        };
        
        if (sizes[size]) {
            chatPanel.style.width = sizes[size] + 'px';
            chatPanel.style.flex = 'none';
            this.onResize();
            this.saveSizes();
        }
    }
};

// Export
window.Panels = Panels;
