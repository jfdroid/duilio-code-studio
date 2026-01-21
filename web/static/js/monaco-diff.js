/**
 * DuilioCode Studio - Monaco Diff Editor
 * Professional side-by-side diff view
 */

const MonacoDiff = {
    diffEditor: null,
    isActive: false,
    originalContent: '',
    
    /**
     * Initialize diff editor (called after Monaco is ready)
     */
    init() {
        console.log('[DuilioCode] Monaco Diff module ready');
    },
    
    /**
     * Set original content for comparison
     */
    setOriginal(content) {
        this.originalContent = content;
    },
    
    /**
     * Toggle diff view
     */
    toggle() {
        if (this.isActive) {
            this.hide();
        } else {
            this.show();
        }
    },
    
    /**
     * Show diff editor
     */
    show() {
        if (typeof monaco === 'undefined') {
            console.error('[DuilioCode] Monaco not loaded');
            Utils.showNotification('Diff editor not available', 'error');
            return;
        }
        
        const monacoContainer = document.getElementById('monacoContainer');
        const diffContainer = document.getElementById('monacoDiffContainer');
        const toggleBtn = document.getElementById('diffToggleBtn');
        
        if (!monacoContainer || !diffContainer) return;
        
        // Get current content from Monaco
        let currentContent = '';
        if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
            currentContent = MonacoEditor.getContent();
        }
        
        // If no original content, use current as original
        if (!this.originalContent) {
            this.originalContent = AppState.editor.originalContent || currentContent;
        }
        
        // Hide normal editor, show diff
        monacoContainer.style.display = 'none';
        diffContainer.style.display = 'block';
        
        // Get language
        const language = AppState.editor.currentFile?.language || 'plaintext';
        const monacoLang = MonacoEditor?.languageMap?.[language] || language;
        
        // Create or update diff editor
        if (!this.diffEditor) {
            this.diffEditor = monaco.editor.createDiffEditor(diffContainer, {
                theme: 'duilio-dark',
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                automaticLayout: true,
                readOnly: false,
                renderSideBySide: true,
                enableSplitViewResizing: true,
                originalEditable: false,
                ignoreTrimWhitespace: false,
                renderIndicators: true,
                renderOverviewRuler: true,
                diffWordWrap: 'off'
            });
        }
        
        // Create models
        const originalModel = monaco.editor.createModel(this.originalContent, monacoLang);
        const modifiedModel = monaco.editor.createModel(currentContent, monacoLang);
        
        // Set models
        this.diffEditor.setModel({
            original: originalModel,
            modified: modifiedModel
        });
        
        // Update button state
        if (toggleBtn) toggleBtn.classList.add('active');
        this.isActive = true;
        
        // Show change summary
        setTimeout(() => this.showChangeSummary(), 100);
    },
    
    /**
     * Hide diff editor
     */
    hide() {
        const monacoContainer = document.getElementById('monacoContainer');
        const diffContainer = document.getElementById('monacoDiffContainer');
        const toggleBtn = document.getElementById('diffToggleBtn');
        
        if (!monacoContainer || !diffContainer) return;
        
        // Get content from diff editor if it exists
        if (this.diffEditor) {
            const modifiedContent = this.diffEditor.getModifiedEditor().getValue();
            
            // Update Monaco editor with modified content
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.editor.setValue(modifiedContent);
            }
        }
        
        // Show normal editor, hide diff
        diffContainer.style.display = 'none';
        monacoContainer.style.display = 'block';
        
        // Update button state
        if (toggleBtn) toggleBtn.classList.remove('active');
        this.isActive = false;
        
        // Resize Monaco
        if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
            MonacoEditor.resize();
        }
    },
    
    /**
     * Show change summary notification
     */
    showChangeSummary() {
        if (!this.diffEditor) return;
        
        const lineChanges = this.diffEditor.getLineChanges();
        if (!lineChanges) return;
        
        let added = 0;
        let removed = 0;
        
        lineChanges.forEach(change => {
            if (change.originalStartLineNumber === 0) {
                added += change.modifiedEndLineNumber - change.modifiedStartLineNumber + 1;
            } else if (change.modifiedStartLineNumber === 0) {
                removed += change.originalEndLineNumber - change.originalStartLineNumber + 1;
            } else {
                added += change.modifiedEndLineNumber - change.modifiedStartLineNumber + 1;
                removed += change.originalEndLineNumber - change.originalStartLineNumber + 1;
            }
        });
        
        if (added > 0 || removed > 0) {
            Utils.showNotification(`Changes: +${added} -${removed} lines`, 'info');
        } else {
            Utils.showNotification('No changes detected', 'info');
        }
    },
    
    /**
     * Get modified content
     */
    getModifiedContent() {
        if (!this.diffEditor) return '';
        return this.diffEditor.getModifiedEditor().getValue();
    },
    
    /**
     * Dispose diff editor
     */
    dispose() {
        if (this.diffEditor) {
            this.diffEditor.dispose();
            this.diffEditor = null;
        }
        this.isActive = false;
    }
};

// Export
window.MonacoDiff = MonacoDiff;
