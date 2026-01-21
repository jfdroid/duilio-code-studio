/**
 * DuilioCode Studio - Diff Module
 * Shows visual diff between original and modified content
 */

const DiffViewer = {
    isActive: false,
    originalContent: '',
    
    /**
     * Store original content when file is opened
     */
    setOriginal(content) {
        this.originalContent = content;
    },
    
    /**
     * Get current content from editor
     */
    getCurrentContent() {
        const editor = document.getElementById('codeEditor');
        return editor ? editor.value : '';
    },
    
    /**
     * Toggle diff view
     */
    toggle() {
        this.isActive = !this.isActive;
        
        const editorContent = document.getElementById('editorContent');
        const toggleBtn = document.getElementById('diffToggleBtn');
        
        if (this.isActive) {
            this.show();
            if (toggleBtn) toggleBtn.classList.add('active');
        } else {
            this.hide();
            if (toggleBtn) toggleBtn.classList.remove('active');
        }
    },
    
    /**
     * Show diff view
     */
    show() {
        const editorContent = document.getElementById('editorContent');
        const editor = document.getElementById('codeEditor');
        
        if (!editorContent || !this.originalContent) return;
        
        // Get current content
        const currentContent = editor ? editor.value : '';
        
        // Generate diff
        const diffHtml = this.generateDiff(this.originalContent, currentContent);
        
        // Hide editor, show diff
        if (editor) editor.style.display = 'none';
        
        // Create or update diff container
        let diffContainer = document.getElementById('diffView');
        if (!diffContainer) {
            diffContainer = document.createElement('div');
            diffContainer.id = 'diffView';
            diffContainer.className = 'diff-container';
            editorContent.appendChild(diffContainer);
        }
        
        diffContainer.innerHTML = diffHtml;
        diffContainer.style.display = 'block';
    },
    
    /**
     * Hide diff view
     */
    hide() {
        const editor = document.getElementById('codeEditor');
        const diffView = document.getElementById('diffView');
        
        if (editor) editor.style.display = 'block';
        if (diffView) diffView.style.display = 'none';
    },
    
    /**
     * Generate diff HTML from two strings
     */
    generateDiff(original, current) {
        const originalLines = original.split('\n');
        const currentLines = current.split('\n');
        
        // Simple diff algorithm (line-by-line comparison)
        const diff = this.computeDiff(originalLines, currentLines);
        
        let html = '';
        let lineNum = 1;
        
        for (const item of diff) {
            if (item.type === 'unchanged') {
                html += `
                    <div class="diff-line unchanged">
                        <span class="diff-line-number">${lineNum}</span>
                        <span class="diff-line-content">${this.escapeHtml(item.content)}</span>
                    </div>`;
                lineNum++;
            } else if (item.type === 'removed') {
                html += `
                    <div class="diff-line removed">
                        <span class="diff-line-number">-</span>
                        <span class="diff-line-content">${this.escapeHtml(item.content)}</span>
                    </div>`;
            } else if (item.type === 'added') {
                html += `
                    <div class="diff-line added">
                        <span class="diff-line-number">${lineNum}</span>
                        <span class="diff-line-content">${this.escapeHtml(item.content)}</span>
                    </div>`;
                lineNum++;
            }
        }
        
        return html || '<div class="diff-line unchanged"><span class="diff-line-number">1</span><span class="diff-line-content">(No changes)</span></div>';
    },
    
    /**
     * Compute diff between two arrays of lines
     * Uses a simple LCS-based approach
     */
    computeDiff(originalLines, currentLines) {
        const result = [];
        
        // Build a map of lines in original
        const originalMap = new Map();
        originalLines.forEach((line, index) => {
            if (!originalMap.has(line)) {
                originalMap.set(line, []);
            }
            originalMap.get(line).push(index);
        });
        
        // Track which original lines have been matched
        const matchedOriginal = new Set();
        const matchedCurrent = new Set();
        
        // First pass: find exact matches
        currentLines.forEach((line, currentIndex) => {
            if (originalMap.has(line)) {
                const originalIndices = originalMap.get(line);
                for (const origIndex of originalIndices) {
                    if (!matchedOriginal.has(origIndex)) {
                        matchedOriginal.add(origIndex);
                        matchedCurrent.add(currentIndex);
                        break;
                    }
                }
            }
        });
        
        // Second pass: build diff output
        let origIndex = 0;
        let currIndex = 0;
        
        while (origIndex < originalLines.length || currIndex < currentLines.length) {
            // Check if current original line was removed
            while (origIndex < originalLines.length && !matchedOriginal.has(origIndex)) {
                result.push({ type: 'removed', content: originalLines[origIndex] });
                origIndex++;
            }
            
            // Check if current new line was added
            while (currIndex < currentLines.length && !matchedCurrent.has(currIndex)) {
                result.push({ type: 'added', content: currentLines[currIndex] });
                currIndex++;
            }
            
            // Output matched line as unchanged
            if (origIndex < originalLines.length && currIndex < currentLines.length) {
                if (matchedOriginal.has(origIndex) && matchedCurrent.has(currIndex)) {
                    result.push({ type: 'unchanged', content: currentLines[currIndex] });
                }
                origIndex++;
                currIndex++;
            }
        }
        
        return result;
    },
    
    /**
     * Check if file has changes
     */
    hasChanges() {
        const current = this.getCurrentContent();
        return current !== this.originalContent;
    },
    
    /**
     * Get change summary
     */
    getChangeSummary() {
        if (!this.originalContent) return null;
        
        const original = this.originalContent.split('\n');
        const current = this.getCurrentContent().split('\n');
        const diff = this.computeDiff(original, current);
        
        const added = diff.filter(d => d.type === 'added').length;
        const removed = diff.filter(d => d.type === 'removed').length;
        
        return { added, removed, total: added + removed };
    },
    
    /**
     * Escape HTML entities
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Export for use in other modules
window.DiffViewer = DiffViewer;
