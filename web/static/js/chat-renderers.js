/**
 * DuilioCode Studio - Chat Renderers
 * Mermaid diagrams and KaTeX math rendering in chat
 */

const ChatRenderers = {
    mermaidId: 0,
    
    /**
     * Initialize renderers
     */
    init() {
        // Initialize Mermaid
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: false,
                theme: 'dark',
                themeVariables: {
                    darkMode: true,
                    background: '#0d1117',
                    primaryColor: '#238636',
                    primaryTextColor: '#e6edf3',
                    primaryBorderColor: '#30363d',
                    lineColor: '#8b949e',
                    secondaryColor: '#21262d',
                    tertiaryColor: '#161b22',
                    noteTextColor: '#e6edf3',
                    noteBkgColor: '#21262d',
                    noteBorderColor: '#30363d',
                    actorTextColor: '#e6edf3',
                    actorBkg: '#21262d',
                    actorBorder: '#30363d',
                    signalColor: '#e6edf3',
                    signalTextColor: '#e6edf3'
                },
                flowchart: {
                    htmlLabels: true,
                    curve: 'basis'
                },
                sequence: {
                    actorMargin: 50,
                    mirrorActors: true
                },
                gantt: {
                    titleTopMargin: 25,
                    barHeight: 20,
                    barGap: 4
                }
            });
            console.log('[DuilioCode] Mermaid initialized');
        }
        
        console.log('[DuilioCode] Chat renderers initialized');
    },
    
    /**
     * Process message content for special rendering
     * Called after basic markdown processing
     */
    processContent(html) {
        // Process Mermaid diagrams
        html = this.processMermaid(html);
        
        // Process KaTeX math
        html = this.processKaTeX(html);
        
        return html;
    },
    
    /**
     * Process Mermaid code blocks
     */
    processMermaid(html) {
        if (typeof mermaid === 'undefined') return html;
        
        // Find mermaid code blocks: ```mermaid ... ```
        const mermaidRegex = /<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/gi;
        
        return html.replace(mermaidRegex, (match, code) => {
            const id = `mermaid-${++this.mermaidId}`;
            const decodedCode = this.decodeHtml(code.trim());
            
            // Return placeholder that will be rendered after DOM insertion
            return `
                <div class="mermaid-container">
                    <div class="mermaid-header">
                        <span class="mermaid-label">Diagram</span>
                        <button class="mermaid-copy" onclick="ChatRenderers.copyMermaidCode('${id}')" title="Copy code">
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                            </svg>
                        </button>
                    </div>
                    <div class="mermaid" id="${id}" data-code="${this.encodeHtml(decodedCode)}">${decodedCode}</div>
                </div>
            `;
        });
    },
    
    /**
     * Process KaTeX math expressions
     */
    processKaTeX(html) {
        if (typeof katex === 'undefined') return html;
        
        // Block math: $$ ... $$
        html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match, math) => {
            try {
                return `<div class="katex-block">${katex.renderToString(math.trim(), {
                    displayMode: true,
                    throwOnError: false
                })}</div>`;
            } catch (e) {
                console.error('[KaTeX] Error:', e);
                return match;
            }
        });
        
        // Inline math: $ ... $ (but not $$ or $ at word boundaries)
        html = html.replace(/(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)/g, (match, math) => {
            try {
                return katex.renderToString(math.trim(), {
                    displayMode: false,
                    throwOnError: false
                });
            } catch (e) {
                console.error('[KaTeX] Error:', e);
                return match;
            }
        });
        
        return html;
    },
    
    /**
     * Render all mermaid diagrams in container
     * Call this after inserting HTML into DOM
     */
    renderMermaidDiagrams(container) {
        if (typeof mermaid === 'undefined') return;
        
        const diagrams = container.querySelectorAll('.mermaid:not(.rendered)');
        
        diagrams.forEach(async (el) => {
            try {
                const code = el.dataset.code ? this.decodeHtml(el.dataset.code) : el.textContent;
                const id = el.id || `mermaid-${++this.mermaidId}`;
                
                // Render
                const { svg } = await mermaid.render(id + '-svg', code);
                el.innerHTML = svg;
                el.classList.add('rendered');
            } catch (error) {
                console.error('[Mermaid] Render error:', error);
                el.innerHTML = `<div class="mermaid-error">Failed to render diagram</div>`;
            }
        });
    },
    
    /**
     * Copy mermaid code
     */
    copyMermaidCode(id) {
        const el = document.getElementById(id);
        if (el && el.dataset.code) {
            navigator.clipboard.writeText(this.decodeHtml(el.dataset.code));
            Utils.showNotification('Diagram code copied', 'success');
        }
    },
    
    /**
     * Encode HTML entities
     */
    encodeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },
    
    /**
     * Decode HTML entities
     */
    decodeHtml(text) {
        const textarea = document.createElement('textarea');
        textarea.innerHTML = text;
        return textarea.value;
    }
};

// Export
window.ChatRenderers = ChatRenderers;
