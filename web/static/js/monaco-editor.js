/**
 * DuilioCode Studio - Monaco Editor Integration
 * Full-featured code editor with syntax highlighting, autocomplete, and more
 */

const MonacoEditor = {
    editor: null,
    isReady: false,
    pendingContent: null,
    pendingLanguage: null,
    originalContent: '',
    
    // Language mapping from file extensions to Monaco language IDs
    languageMap: {
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'java': 'java',
        'kt': 'kotlin',
        'kts': 'kotlin',
        'go': 'go',
        'rs': 'rust',
        'c': 'c',
        'cpp': 'cpp',
        'cc': 'cpp',
        'h': 'c',
        'hpp': 'cpp',
        'cs': 'csharp',
        'php': 'php',
        'swift': 'swift',
        'scala': 'scala',
        'r': 'r',
        'sql': 'sql',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'scss': 'scss',
        'sass': 'scss',
        'less': 'less',
        'json': 'json',
        'xml': 'xml',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'markdown': 'markdown',
        'sh': 'shell',
        'bash': 'shell',
        'zsh': 'shell',
        'dockerfile': 'dockerfile',
        'graphql': 'graphql',
        'gql': 'graphql',
        'lua': 'lua',
        'perl': 'perl',
        'pl': 'perl',
        'ps1': 'powershell',
        'vue': 'html',
        'svelte': 'html',
        'toml': 'ini',
        'ini': 'ini',
        'cfg': 'ini',
        'conf': 'ini',
        'txt': 'plaintext',
        'log': 'plaintext'
    },
    
    /**
     * Initialize Monaco Editor
     */
    async init() {
        return new Promise((resolve, reject) => {
            if (typeof require === 'undefined') {
                console.error('[Monaco] AMD loader not found');
                reject(new Error('Monaco loader not available'));
                return;
            }
            
            require(['vs/editor/editor.main'], () => {
                console.log('[DuilioCode] Monaco Editor loaded');
                
                // Define custom dark theme matching DuilioCode
                monaco.editor.defineTheme('duilio-dark', {
                    base: 'vs-dark',
                    inherit: true,
                    rules: [
                        { token: 'comment', foreground: '6e7681', fontStyle: 'italic' },
                        { token: 'keyword', foreground: 'ff7b72' },
                        { token: 'string', foreground: 'a5d6ff' },
                        { token: 'number', foreground: '79c0ff' },
                        { token: 'type', foreground: 'ffa657' },
                        { token: 'function', foreground: 'd2a8ff' },
                        { token: 'variable', foreground: 'ffa657' },
                        { token: 'constant', foreground: '79c0ff' },
                    ],
                    colors: {
                        'editor.background': '#0d1117',
                        'editor.foreground': '#e6edf3',
                        'editor.lineHighlightBackground': '#161b2233',
                        'editor.selectionBackground': '#264f78',
                        'editor.inactiveSelectionBackground': '#264f7855',
                        'editorLineNumber.foreground': '#484f58',
                        'editorLineNumber.activeForeground': '#e6edf3',
                        'editorCursor.foreground': '#58a6ff',
                        'editor.findMatchBackground': '#ffd33d44',
                        'editor.findMatchHighlightBackground': '#ffd33d22',
                        'editorWidget.background': '#161b22',
                        'editorWidget.border': '#30363d',
                        'editorSuggestWidget.background': '#161b22',
                        'editorSuggestWidget.border': '#30363d',
                        'editorSuggestWidget.selectedBackground': '#21262d',
                        'editorHoverWidget.background': '#161b22',
                        'editorHoverWidget.border': '#30363d',
                        'scrollbarSlider.background': '#484f5833',
                        'scrollbarSlider.hoverBackground': '#484f5866',
                        'scrollbarSlider.activeBackground': '#484f58aa',
                        'minimap.background': '#0d1117',
                    }
                });
                
                // Create editor instance
                const container = document.getElementById('monacoContainer');
                if (!container) {
                    reject(new Error('Monaco container not found'));
                    return;
                }
                
                this.editor = monaco.editor.create(container, {
                    value: '',
                    language: 'plaintext',
                    theme: 'duilio-dark',
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                    fontLigatures: true,
                    lineNumbers: 'on',
                    minimap: { enabled: true, scale: 1 },
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 4,
                    insertSpaces: true,
                    wordWrap: 'off',
                    renderWhitespace: 'selection',
                    bracketPairColorization: { enabled: true },
                    guides: {
                        bracketPairs: true,
                        indentation: true
                    },
                    suggest: {
                        showKeywords: true,
                        showSnippets: true,
                        showClasses: true,
                        showFunctions: true,
                        showVariables: true,
                        showModules: true
                    },
                    quickSuggestions: {
                        other: true,
                        comments: false,
                        strings: true
                    },
                    parameterHints: { enabled: true },
                    folding: true,
                    foldingStrategy: 'indentation',
                    showFoldingControls: 'mouseover',
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    cursorSmoothCaretAnimation: 'on',
                    renderLineHighlight: 'all',
                    contextmenu: true,
                    mouseWheelZoom: true,
                    padding: { top: 10, bottom: 10 }
                });
                
                // Add keyboard shortcuts
                this.setupKeyboardShortcuts();
                
                // Track content changes for modified indicator
                this.editor.onDidChangeModelContent(() => {
                    this.onContentChange();
                });
                
                this.isReady = true;
                
                // If there was pending content, set it now
                if (this.pendingContent !== null) {
                    this.setContent(this.pendingContent, this.pendingLanguage);
                    this.pendingContent = null;
                    this.pendingLanguage = null;
                }
                
                console.log('[DuilioCode] Monaco Editor initialized');
                resolve();
            });
        });
    },
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        // Save file: Ctrl+S
        this.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            if (typeof saveCurrentFile === 'function') {
                saveCurrentFile();
            }
        });
        
        // Close tab: Ctrl+W
        this.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyW, () => {
            if (AppState.editor.currentFile && typeof Tabs !== 'undefined') {
                Tabs.close(AppState.editor.currentFile.path);
            }
        });
    },
    
    /**
     * Handle content change
     */
    onContentChange() {
        const currentContent = this.getContent();
        const isModified = currentContent !== this.originalContent;
        
        // Update tab modified indicator
        if (AppState.editor.currentFile) {
            const tab = document.querySelector(`.tab[data-path="${AppState.editor.currentFile.path}"]`);
            if (tab) {
                tab.classList.toggle('modified', isModified);
            }
        }
        
        // Update DiffViewer if active
        if (typeof DiffViewer !== 'undefined' && DiffViewer.isActive) {
            DiffViewer.show();
        }
    },
    
    /**
     * Set editor content
     */
    setContent(content, language = 'plaintext') {
        if (!this.isReady) {
            this.pendingContent = content;
            this.pendingLanguage = language;
            return;
        }
        
        // Map language to Monaco language ID
        const monacoLang = this.languageMap[language] || language || 'plaintext';
        
        // Set content and language
        const model = this.editor.getModel();
        if (model) {
            monaco.editor.setModelLanguage(model, monacoLang);
            this.editor.setValue(content || '');
        }
        
        // Store original for diff
        this.originalContent = content || '';
        
        // Update DiffViewer
        if (typeof DiffViewer !== 'undefined') {
            DiffViewer.setOriginal(content || '');
        }
        
        // Focus editor
        this.editor.focus();
    },
    
    /**
     * Get editor content
     */
    getContent() {
        if (!this.isReady || !this.editor) {
            const textarea = document.getElementById('codeEditor');
            return textarea ? textarea.value : '';
        }
        return this.editor.getValue();
    },
    
    /**
     * Get language from file extension
     */
    getLanguageFromPath(path) {
        if (!path) return 'plaintext';
        const ext = path.split('.').pop().toLowerCase();
        return this.languageMap[ext] || 'plaintext';
    },
    
    /**
     * Set language
     */
    setLanguage(language) {
        if (!this.isReady || !this.editor) return;
        
        const monacoLang = this.languageMap[language] || language || 'plaintext';
        const model = this.editor.getModel();
        if (model) {
            monaco.editor.setModelLanguage(model, monacoLang);
        }
    },
    
    /**
     * Focus editor
     */
    focus() {
        if (this.isReady && this.editor) {
            this.editor.focus();
        }
    },
    
    /**
     * Go to specific line
     */
    goToLine(lineNumber) {
        if (!this.isReady || !this.editor) return;
        
        this.editor.revealLineInCenter(lineNumber);
        this.editor.setPosition({ lineNumber, column: 1 });
        this.editor.focus();
    },
    
    /**
     * Insert text at cursor
     */
    insertText(text) {
        if (!this.isReady || !this.editor) return;
        
        const selection = this.editor.getSelection();
        this.editor.executeEdits('insert', [{
            range: selection,
            text: text,
            forceMoveMarkers: true
        }]);
    },
    
    /**
     * Replace all content (for applying code from chat)
     */
    replaceAll(content) {
        if (!this.isReady || !this.editor) return;
        
        const fullRange = this.editor.getModel().getFullModelRange();
        this.editor.executeEdits('replace', [{
            range: fullRange,
            text: content,
            forceMoveMarkers: true
        }]);
    },
    
    /**
     * Format document
     */
    format() {
        if (!this.isReady || !this.editor) return;
        this.editor.getAction('editor.action.formatDocument').run();
    },
    
    /**
     * Toggle word wrap
     */
    toggleWordWrap() {
        if (!this.isReady || !this.editor) return;
        
        const currentValue = this.editor.getOption(monaco.editor.EditorOption.wordWrap);
        this.editor.updateOptions({ 
            wordWrap: currentValue === 'off' ? 'on' : 'off' 
        });
    },
    
    /**
     * Toggle minimap
     */
    toggleMinimap() {
        if (!this.isReady || !this.editor) return;
        
        const options = this.editor.getOptions();
        const minimapEnabled = options.get(monaco.editor.EditorOption.minimap).enabled;
        this.editor.updateOptions({ 
            minimap: { enabled: !minimapEnabled } 
        });
    },
    
    /**
     * Resize editor
     */
    resize() {
        if (this.isReady && this.editor) {
            this.editor.layout();
        }
    },
    
    /**
     * Dispose editor
     */
    dispose() {
        if (this.editor) {
            this.editor.dispose();
            this.editor = null;
            this.isReady = false;
        }
    }
};

// Export for global access
window.MonacoEditor = MonacoEditor;
