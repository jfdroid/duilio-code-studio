/**
 * DuilioCode Studio - Configuration
 * Global constants and configuration
 */

const CONFIG = {
    // API Configuration
    API_BASE: '',
    
    // Default Model
    DEFAULT_MODEL: 'qwen2.5-coder:14b',
    
    // Auto-save interval (ms)
    AUTOSAVE_INTERVAL: 30000,
    
    // Connection check interval (ms)
    CONNECTION_CHECK_INTERVAL: 30000,
    
    // File Icons by extension
    FILE_ICONS: {
        'py': '🐍', 'js': '📜', 'ts': '💠', 'jsx': '⚛️', 'tsx': '⚛️',
        'kt': '🟣', 'java': '☕', 'go': '🐹', 'rs': '🦀', 'cpp': '⚙️', 'c': '⚙️',
        'html': '🌐', 'css': '🎨', 'scss': '🎨', 'json': '📋', 'yaml': '📋', 'yml': '📋',
        'md': '📝', 'txt': '📄', 'sh': '💻', 'bash': '💻',
        'sql': '🗃️', 'xml': '📰', 'svg': '🖼️', 'png': '🖼️', 'jpg': '🖼️',
        'pdf': '📕', 'zip': '📦', 'tar': '📦', 'gz': '📦',
        'swift': '🍎', 'rb': '💎', 'php': '🐘', 'vue': '💚', 'svelte': '🔥'
    },
    
    // Keyboard Shortcuts
    SHORTCUTS: {
        SAVE: { key: 's', ctrl: true },
        OPEN_FOLDER: { key: 'o', ctrl: true },
        NEW_FILE: { key: 'n', ctrl: true },
        TOGGLE_EXPLORER: { key: 'b', ctrl: true },
        SEND_MESSAGE: { key: 'Enter', ctrl: true }
    }
};

// Freeze config to prevent modifications
Object.freeze(CONFIG);
Object.freeze(CONFIG.FILE_ICONS);
Object.freeze(CONFIG.SHORTCUTS);
