/**
 * DuilioCode Studio - Utility Functions
 * Helper functions and utilities
 */

const Utils = {
    /**
     * Shorten path by replacing home directory with ~
     * @param {string} path - Path to shorten
     * @returns {string} Shortened path or original if not in home
     */
    shortenPath(path) {
        // Guard against undefined/null path
        if (!path || typeof path !== 'string') {
            return path || '';
        }
        
        const home = AppState?.workspace?.homeDirectory || '';
        if (home && path.startsWith(home)) {
            return '~' + path.slice(home.length);
        }
        return path;
    },
    
    /**
     * Get file icon SVG based on extension
     */
    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const type = CONFIG.FILE_ICONS[ext] || 'file';
        
        // Return SVG icon based on file type
        const icons = {
            'py': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'js': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'ts': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'html': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'css': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'json': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-orange)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'md': '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
            'file': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
        };
        
        return icons[type] || icons['file'];
    },
    
    /**
     * Get file language from extension
     */
    getLanguage(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const map = {
            'py': 'python', 'js': 'javascript', 'ts': 'typescript',
            'jsx': 'jsx', 'tsx': 'tsx', 'kt': 'kotlin', 'java': 'java',
            'go': 'go', 'rs': 'rust', 'cpp': 'cpp', 'c': 'c',
            'html': 'html', 'css': 'css', 'scss': 'scss',
            'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
            'md': 'markdown', 'sql': 'sql', 'sh': 'bash'
        };
        return map[ext] || 'plaintext';
    },
    
    /**
     * Format file size
     */
    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    },
    
    /**
     * Format timestamp
     */
    formatTime(date = new Date()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    /**
     * Normalize file path - resolve relative paths and avoid duplication
     * @param {string} filePath - Path from AI or user input
     * @param {string} workspacePath - Current workspace path
     * @returns {string} Normalized absolute path
     */
    normalizeFilePath(filePath, workspacePath) {
        if (!filePath || typeof filePath !== 'string') {
            return filePath || '';
        }
        
        // Trim whitespace
        filePath = filePath.trim();
        
        // CRITICAL: Check if path looks like an absolute path (starts with /Users, /home, /var, etc.)
        // but is missing the leading slash
        const absolutePathPatterns = [
            /^Users\//,
            /^home\//,
            /^var\//,
            /^tmp\//,
            /^opt\//,
            /^etc\//,
            /^root\//,
            /^[A-Z]:\\/,  // Windows drive letter
        ];
        
        const looksLikeAbsolute = absolutePathPatterns.some(pattern => pattern.test(filePath));
        if (looksLikeAbsolute && !filePath.startsWith('/')) {
            // This is an absolute path missing the leading slash
            filePath = '/' + filePath;
        }
        
        // If no workspace, return path as-is (or make absolute if starts with /)
        if (!workspacePath) {
            return filePath.startsWith('/') ? filePath : `/${filePath}`;
        }
        
        // Normalize workspace path (remove trailing slash, ensure starts with /)
        const normalizedWorkspace = workspacePath.replace(/\/+$/, '').replace(/^\/+/, '/');
        const workspaceWithoutSlash = normalizedWorkspace.replace(/^\/+/, '');
        
        // Remove leading ./ from filePath
        let cleanPath = filePath.replace(/^\.\//, '');
        
        // CRITICAL: If path starts with /Users, /home, etc., it's an absolute path
        // Use it as-is (don't try to join with workspace)
        if (cleanPath.startsWith('/')) {
            // Already absolute path - normalize slashes and return
            return cleanPath.replace(/\/+/g, '/');
        }
        
        // CRITICAL: Check if path already contains workspace (avoid duplication)
        // Check multiple variations to catch all cases
        const pathVariations = [
            cleanPath,
            '/' + cleanPath,
            cleanPath.replace(/^\/+/, ''),
            '/' + cleanPath.replace(/^\/+/, '')
        ];
        
        for (const pathVar of pathVariations) {
            // Check if this variation contains the workspace
            if (pathVar.includes(normalizedWorkspace) || pathVar.includes(workspaceWithoutSlash)) {
                // Path contains workspace - find where it starts and use from there
                let normalized = pathVar;
                
                // Find first occurrence of workspace
                const workspaceIndex = normalized.indexOf(normalizedWorkspace);
                const workspaceNoSlashIndex = normalized.indexOf(workspaceWithoutSlash);
                
                let startIndex = -1;
                if (workspaceIndex >= 0) {
                    startIndex = workspaceIndex;
                } else if (workspaceNoSlashIndex >= 0) {
                    startIndex = workspaceNoSlashIndex;
                    normalized = '/' + normalized; // Add leading slash
                    startIndex++; // Adjust for added slash
                }
                
                if (startIndex >= 0) {
                    // Extract from workspace onwards
                    normalized = normalized.substring(startIndex);
                } else {
                    // Ensure starts with /
                    if (!normalized.startsWith('/')) {
                        normalized = '/' + normalized;
                    }
                }
                
                // Remove any duplicate workspace segments
                const escapedWorkspace = normalizedWorkspace.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const escapedNoSlash = workspaceWithoutSlash.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                
                // Remove duplicates: /workspace/workspace -> /workspace
                normalized = normalized.replace(new RegExp(`(${escapedWorkspace})/+(${escapedWorkspace})`, 'g'), '$1');
                normalized = normalized.replace(new RegExp(`(${escapedNoSlash})/+(${escapedNoSlash})`, 'g'), '$1');
                normalized = normalized.replace(new RegExp(`(${escapedWorkspace})/+(${escapedNoSlash})`, 'g'), '$1');
                normalized = normalized.replace(new RegExp(`(${escapedNoSlash})/+(${escapedWorkspace})`, 'g'), '$1');
                
                // Normalize slashes
                normalized = normalized.replace(/\/+/g, '/');
                
                // CRITICAL: Ensure it starts with /
                if (!normalized.startsWith('/')) {
                    normalized = '/' + normalized;
                }
                
                return normalized;
            }
        }
        
        // Path doesn't contain workspace - treat as relative or absolute
        if (cleanPath.startsWith('/')) {
            // Already absolute path
            // If it's clearly outside workspace (doesn't start with workspace path), use as-is
            if (!cleanPath.startsWith(normalizedWorkspace)) {
                // This is an absolute path outside the workspace (e.g., /Users/username/Desktop/file.txt)
                // Return as-is - user explicitly requested this location
                return cleanPath.replace(/\/+/g, '/');
            }
            // If it starts with workspace but wasn't caught above, use as-is
            return cleanPath.replace(/\/+/g, '/');
        }
        
        // Relative path - join with workspace
        const result = `${normalizedWorkspace}/${cleanPath}`.replace(/\/+/g, '/');
        
        // CRITICAL: Ensure result always starts with /
        return result.startsWith('/') ? result : '/' + result;
    },
    
    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 3000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification--${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 13px;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.borderColor = 'var(--accent-green)';
        } else if (type === 'error') {
            notification.style.borderColor = 'var(--accent-red)';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
};
