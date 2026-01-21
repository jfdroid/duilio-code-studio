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
    
    // File Icons by extension (using SVG icons via CSS classes instead of emojis)
    FILE_ICONS: {
        // Languages
        'py': 'py', 'js': 'js', 'ts': 'ts', 'jsx': 'jsx', 'tsx': 'tsx',
        'kt': 'kt', 'java': 'java', 'go': 'go', 'rs': 'rs', 'cpp': 'cpp', 'c': 'c',
        'html': 'html', 'css': 'css', 'scss': 'scss', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
        'md': 'md', 'txt': 'txt', 'sh': 'sh', 'bash': 'sh',
        'sql': 'sql', 'xml': 'xml', 'svg': 'svg', 'png': 'img', 'jpg': 'img',
        'pdf': 'pdf', 'zip': 'zip', 'tar': 'zip', 'gz': 'zip',
        'swift': 'swift', 'rb': 'rb', 'php': 'php', 'vue': 'vue', 'svelte': 'svelte'
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
