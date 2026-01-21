/**
 * DuilioCode Studio - Terminal Module
 * Integrated terminal using xterm.js
 */

const Terminal = {
    instances: [],
    activeTerminal: null,
    isVisible: false,
    split: null,
    
    /**
     * Initialize terminal system
     */
    async init() {
        if (typeof window.Terminal === 'undefined' || !window.Terminal) {
            console.warn('[DuilioCode] xterm.js not loaded');
            return;
        }
        
        console.log('[DuilioCode] Terminal module initialized');
    },
    
    /**
     * Create a new terminal instance
     */
    createNew() {
        if (typeof window.Terminal === 'undefined') {
            Utils.showNotification('Terminal not available', 'error');
            return null;
        }
        
        const terminalId = this.instances.length + 1;
        
        // Create xterm instance
        const term = new window.Terminal({
            theme: {
                background: '#0d1117',
                foreground: '#e6edf3',
                cursor: '#58a6ff',
                cursorAccent: '#0d1117',
                selectionBackground: '#264f78',
                black: '#484f58',
                red: '#ff7b72',
                green: '#3fb950',
                yellow: '#d29922',
                blue: '#58a6ff',
                magenta: '#bc8cff',
                cyan: '#39c5cf',
                white: '#b1bac4',
                brightBlack: '#6e7681',
                brightRed: '#ffa198',
                brightGreen: '#56d364',
                brightYellow: '#e3b341',
                brightBlue: '#79c0ff',
                brightMagenta: '#d2a8ff',
                brightCyan: '#56d4dd',
                brightWhite: '#f0f6fc'
            },
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontSize: 13,
            lineHeight: 1.4,
            cursorBlink: true,
            cursorStyle: 'bar',
            scrollback: 10000,
            tabStopWidth: 4
        });
        
        // Store instance
        const instance = {
            id: terminalId,
            term: term,
            inputBuffer: '',
            history: [],
            historyIndex: -1,
            cwd: AppState.workspace.currentPath || '~'
        };
        
        this.instances.push(instance);
        
        // Add tab
        this.addTab(terminalId);
        
        // If first terminal, show panel and open it
        if (this.instances.length === 1) {
            this.show();
            this.openTerminal(terminalId);
        }
        
        return instance;
    },
    
    /**
     * Open terminal in container
     */
    openTerminal(id) {
        const instance = this.instances.find(t => t.id === id);
        if (!instance) return;
        
        const container = document.getElementById('terminalContainer');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Open terminal
        instance.term.open(container);
        
        // Fit to container
        if (typeof FitAddon !== 'undefined') {
            const fitAddon = new FitAddon.FitAddon();
            instance.term.loadAddon(fitAddon);
            instance.fitAddon = fitAddon;
            setTimeout(() => fitAddon.fit(), 100);
        }
        
        // Web links addon
        if (typeof WebLinksAddon !== 'undefined') {
            const webLinksAddon = new WebLinksAddon.WebLinksAddon();
            instance.term.loadAddon(webLinksAddon);
        }
        
        // Setup input handler
        this.setupInputHandler(instance);
        
        // Write welcome message
        if (!instance.welcomed) {
            this.writeWelcome(instance);
            instance.welcomed = true;
        }
        
        // Update active
        this.activeTerminal = instance;
        this.updateTabs(id);
        
        // Focus
        instance.term.focus();
    },
    
    /**
     * Setup input handler for pseudo-terminal
     */
    setupInputHandler(instance) {
        const term = instance.term;
        
        term.onKey(({ key, domEvent }) => {
            const printable = !domEvent.altKey && !domEvent.ctrlKey && !domEvent.metaKey;
            
            if (domEvent.keyCode === 13) { // Enter
                term.write('\r\n');
                this.executeCommand(instance, instance.inputBuffer);
                instance.inputBuffer = '';
            } else if (domEvent.keyCode === 8) { // Backspace
                if (instance.inputBuffer.length > 0) {
                    instance.inputBuffer = instance.inputBuffer.slice(0, -1);
                    term.write('\b \b');
                }
            } else if (domEvent.keyCode === 38) { // Arrow Up
                if (instance.history.length > 0) {
                    if (instance.historyIndex < instance.history.length - 1) {
                        instance.historyIndex++;
                        this.replaceInput(instance, instance.history[instance.history.length - 1 - instance.historyIndex]);
                    }
                }
            } else if (domEvent.keyCode === 40) { // Arrow Down
                if (instance.historyIndex > 0) {
                    instance.historyIndex--;
                    this.replaceInput(instance, instance.history[instance.history.length - 1 - instance.historyIndex]);
                } else if (instance.historyIndex === 0) {
                    instance.historyIndex = -1;
                    this.replaceInput(instance, '');
                }
            } else if (domEvent.ctrlKey && domEvent.keyCode === 67) { // Ctrl+C
                term.write('^C\r\n');
                instance.inputBuffer = '';
                this.writePrompt(instance);
            } else if (domEvent.ctrlKey && domEvent.keyCode === 76) { // Ctrl+L
                term.clear();
                this.writePrompt(instance);
            } else if (printable) {
                instance.inputBuffer += key;
                term.write(key);
            }
        });
        
        // Handle paste
        term.onData(data => {
            // Filter out control sequences
            if (data.length > 1 && !data.includes('\x1b')) {
                instance.inputBuffer += data;
                term.write(data);
            }
        });
    },
    
    /**
     * Replace current input
     */
    replaceInput(instance, newInput) {
        const term = instance.term;
        // Clear current input
        term.write('\r\x1b[K');
        this.writePromptText(instance);
        // Write new input
        instance.inputBuffer = newInput;
        term.write(newInput);
    },
    
    /**
     * Execute command
     */
    async executeCommand(instance, command) {
        const cmd = command.trim();
        
        if (!cmd) {
            this.writePrompt(instance);
            return;
        }
        
        // Add to history
        instance.history.push(cmd);
        instance.historyIndex = -1;
        
        // Handle built-in commands
        if (cmd === 'clear' || cmd === 'cls') {
            instance.term.clear();
            this.writePrompt(instance);
            return;
        }
        
        if (cmd === 'pwd') {
            instance.term.writeln(instance.cwd);
            this.writePrompt(instance);
            return;
        }
        
        if (cmd.startsWith('cd ')) {
            const path = cmd.substring(3).trim();
            await this.changeDirectory(instance, path);
            return;
        }
        
        if (cmd === 'help') {
            this.writeHelp(instance);
            return;
        }
        
        // Execute via API
        try {
            const response = await API.post('/api/tools/execute', {
                code: cmd,
                language: 'shell',
                cwd: instance.cwd
            });
            
            if (response.output) {
                instance.term.writeln(response.output);
            }
            if (response.error) {
                instance.term.writeln(`\x1b[31m${response.error}\x1b[0m`);
            }
        } catch (error) {
            instance.term.writeln(`\x1b[31mError: ${error.message || 'Command failed'}\x1b[0m`);
        }
        
        this.writePrompt(instance);
    },
    
    /**
     * Change directory
     */
    async changeDirectory(instance, path) {
        let newPath = path;
        
        if (path === '~') {
            newPath = AppState.workspace.homeDirectory || '/Users';
        } else if (path === '..') {
            newPath = instance.cwd.split('/').slice(0, -1).join('/') || '/';
        } else if (!path.startsWith('/')) {
            newPath = `${instance.cwd}/${path}`;
        }
        
        // Verify path exists via API
        try {
            const response = await API.get(`/api/files/info?path=${encodeURIComponent(newPath)}`);
            if (response.exists && response.is_directory) {
                instance.cwd = newPath;
            } else {
                instance.term.writeln(`\x1b[31mcd: ${path}: No such directory\x1b[0m`);
            }
        } catch (error) {
            instance.term.writeln(`\x1b[31mcd: ${path}: No such directory\x1b[0m`);
        }
        
        this.writePrompt(instance);
    },
    
    /**
     * Write welcome message
     */
    writeWelcome(instance) {
        const term = instance.term;
        term.writeln('\x1b[36m╭─────────────────────────────────────╮\x1b[0m');
        term.writeln('\x1b[36m│\x1b[0m   \x1b[1;33mDuilioCode Terminal\x1b[0m              \x1b[36m│\x1b[0m');
        term.writeln('\x1b[36m│\x1b[0m   Type "help" for commands         \x1b[36m│\x1b[0m');
        term.writeln('\x1b[36m╰─────────────────────────────────────╯\x1b[0m');
        term.writeln('');
        this.writePrompt(instance);
    },
    
    /**
     * Write help
     */
    writeHelp(instance) {
        const term = instance.term;
        term.writeln('\x1b[1;36mAvailable Commands:\x1b[0m');
        term.writeln('  \x1b[33mclear\x1b[0m      - Clear terminal');
        term.writeln('  \x1b[33mpwd\x1b[0m        - Print working directory');
        term.writeln('  \x1b[33mcd <path>\x1b[0m  - Change directory');
        term.writeln('  \x1b[33mls\x1b[0m         - List files');
        term.writeln('  \x1b[33mcat <file>\x1b[0m - Show file contents');
        term.writeln('  \x1b[33mhelp\x1b[0m       - Show this help');
        term.writeln('');
        term.writeln('\x1b[1;36mKeyboard Shortcuts:\x1b[0m');
        term.writeln('  \x1b[33mCtrl+C\x1b[0m     - Cancel command');
        term.writeln('  \x1b[33mCtrl+L\x1b[0m     - Clear screen');
        term.writeln('  \x1b[33m↑/↓\x1b[0m        - Command history');
        term.writeln('');
        this.writePrompt(instance);
    },
    
    /**
     * Write prompt
     */
    writePrompt(instance) {
        this.writePromptText(instance);
    },
    
    /**
     * Write prompt text
     */
    writePromptText(instance) {
        const shortPath = instance.cwd.replace(AppState.workspace.homeDirectory || '', '~');
        instance.term.write(`\x1b[32m${shortPath}\x1b[0m \x1b[36m❯\x1b[0m `);
    },
    
    /**
     * Add terminal tab
     */
    addTab(id) {
        const tabsContainer = document.querySelector('.terminal-tabs');
        if (!tabsContainer) return;
        
        const newBtn = tabsContainer.querySelector('.terminal-tab-new');
        const tab = document.createElement('button');
        tab.className = 'terminal-tab';
        tab.dataset.terminal = id;
        tab.textContent = `Terminal ${id}`;
        tab.onclick = () => this.openTerminal(id);
        
        tabsContainer.insertBefore(tab, newBtn);
    },
    
    /**
     * Update active tab
     */
    updateTabs(activeId) {
        document.querySelectorAll('.terminal-tab').forEach(tab => {
            tab.classList.toggle('active', parseInt(tab.dataset.terminal) === activeId);
        });
    },
    
    /**
     * Show terminal panel
     */
    show() {
        const panel = document.getElementById('terminalPanel');
        if (!panel) return;
        
        panel.style.display = 'flex';
        this.isVisible = true;
        
        // Initialize vertical split via Panels module
        if (typeof Panels !== 'undefined') {
            Panels.initEditorTerminalSplit();
        }
        
        // Create first terminal if none exists
        if (this.instances.length === 0) {
            this.createNew();
        } else if (this.activeTerminal) {
            // Fit existing terminal
            setTimeout(() => {
                if (this.activeTerminal.fitAddon) {
                    this.activeTerminal.fitAddon.fit();
                }
                this.activeTerminal.term.focus();
            }, 100);
        }
    },
    
    /**
     * Hide terminal panel
     */
    hide() {
        const panel = document.getElementById('terminalPanel');
        if (panel) {
            panel.style.display = 'none';
        }
        this.isVisible = false;
        
        // Destroy the vertical split
        if (typeof Panels !== 'undefined') {
            Panels.destroyEditorTerminalSplit();
        }
    },
    
    /**
     * Toggle terminal visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    },
    
    /**
     * Clear active terminal
     */
    clear() {
        if (this.activeTerminal) {
            this.activeTerminal.term.clear();
            this.writePrompt(this.activeTerminal);
        }
    },
    
    /**
     * Write to terminal
     */
    write(text) {
        if (this.activeTerminal) {
            this.activeTerminal.term.writeln(text);
        }
    }
};

// Export
window.Terminal = Terminal;
