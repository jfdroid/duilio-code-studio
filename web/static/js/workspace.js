/**
 * DuilioCode Studio - Workspace Module
 * Workspace and file tree management
 */

const Workspace = {
    /**
     * Initialize workspace
     */
    async init() {
        try {
            const data = await API.getWorkspace();
            
            // Update state with safe defaults
            AppState.setWorkspace({
                currentPath: data.path || null,
                recentPaths: data.recent_paths || [],
                homeDirectory: data.home_directory || ''
            });
            
            if (data.path && data.exists) {
                document.getElementById('workspacePathText').textContent = Utils.shortenPath(data.path);
                await this.loadFileTree(data.path);
            }
        } catch (error) {
            console.error('Failed to load workspace:', error);
            // Set default state on error
            AppState.setWorkspace({
                currentPath: null,
                recentPaths: [],
                homeDirectory: ''
            });
        }
    },
    
    /**
     * Open workspace modal
     */
    openModal() {
        document.getElementById('workspaceInput').value = AppState.workspace.currentPath || '';
        this.renderRecentFolders();
        document.getElementById('workspaceModal').classList.add('active');
        setTimeout(() => document.getElementById('workspaceInput').focus(), 100);
    },
    
    /**
     * Close workspace modal
     */
    closeModal() {
        document.getElementById('workspaceModal').classList.remove('active');
        PathAutocomplete.hide();
    },
    
    /**
     * Open workspace at path
     */
    async open() {
        const path = document.getElementById('workspaceInput').value.trim();
        if (!path) {
            alert('Please enter a folder path');
            return;
        }
        
        try {
            const data = await API.setWorkspace(path);
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to open workspace');
            }
            
            AppState.setWorkspace({
                currentPath: data.path,
                recentPaths: data.recent_paths || [],
                homeDirectory: data.home_directory || AppState.workspace.homeDirectory || ''
            });
            
            document.getElementById('workspacePathText').textContent = Utils.shortenPath(data.path);
            await this.loadFileTree(data.path);
            this.closeModal();
            
            Utils.showNotification(`Opened: ${Utils.shortenPath(data.path)}`, 'success');
        } catch (error) {
            alert('Error: ' + (error.message || 'Failed to open folder'));
        }
    },
    
    /**
     * Load file tree
     */
    async loadFileTree(path) {
        try {
            const tree = await API.getWorkspaceTree(path, 3);
            this.renderFileTree(tree);
        } catch (error) {
            console.error('Failed to load file tree:', error);
        }
    },
    
    /**
     * Render file tree
     */
    renderFileTree(node, container = null) {
        if (!container) {
            container = document.getElementById('fileTree');
            container.innerHTML = '';
        }
        
        if (!node || !node.children) return;
        
        // Sort: folders first, then files
        const sorted = [...node.children].sort((a, b) => {
            if (a.is_directory && !b.is_directory) return -1;
            if (!a.is_directory && b.is_directory) return 1;
            return a.name.localeCompare(b.name);
        });
        
        sorted.forEach(item => {
            const div = document.createElement('div');
            div.className = `tree-item ${item.is_directory ? 'folder' : 'file'}`;
            div.dataset.path = item.path;
            div.dataset.isDir = item.is_directory;
            
            const folderIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>';
            const icon = item.is_directory ? folderIcon : Utils.getFileIcon(item.name);
            
            div.innerHTML = `
                <span class="tree-item-icon">${icon}</span>
                <span class="tree-item-name">${item.name}</span>
                <div class="tree-item-actions">
                    ${item.is_directory ? `<button class="tree-action" onclick="event.stopPropagation(); FileManager.createInFolder('${item.path}')">+</button>` : ''}
                </div>
            `;
            
            div.onclick = (e) => {
                e.stopPropagation();
                if (item.is_directory) {
                    this.toggleFolder(div, item);
                } else {
                    FileManager.open(item.path);
                }
            };
            
            container.appendChild(div);
            
            if (item.is_directory && item.children && item.children.length > 0) {
                const childContainer = document.createElement('div');
                childContainer.className = 'tree-children collapsed';
                childContainer.id = `children-${item.path.replace(/[^a-zA-Z0-9]/g, '_')}`;
                container.appendChild(childContainer);
                this.renderFileTree(item, childContainer);
            }
        });
    },
    
    /**
     * Toggle folder expansion with lazy loading
     */
    async toggleFolder(element, item) {
        const childId = `children-${item.path.replace(/[^a-zA-Z0-9]/g, '_')}`;
        let childContainer = document.getElementById(childId);
        
        const icon = element.querySelector('.tree-item-icon');
        const closedFolder = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>';
        const openFolder = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><path d="M22 10H2"/></svg>';
        
        // If no child container exists, we need to lazy load
        if (!childContainer) {
            // Show loading state
            icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>';
            
            try {
                // Load children from API
                const tree = await API.getWorkspaceTree(item.path, 2);
                
                if (tree && tree.children && tree.children.length > 0) {
                    // Create child container
                    childContainer = document.createElement('div');
                    childContainer.className = 'tree-children';
                    childContainer.id = childId;
                    element.after(childContainer);
                    
                    // Render children
                    this.renderFileTree(tree, childContainer);
                    icon.innerHTML = openFolder;
                    element.classList.add('expanded');
                } else {
                    // Empty folder
                    icon.innerHTML = closedFolder;
                    Utils.showNotification('Folder is empty', 'info');
                }
            } catch (error) {
                console.error('Error loading folder:', error);
                icon.innerHTML = closedFolder;
                Utils.showNotification('Error loading folder', 'error');
            }
        } else {
            // Toggle existing container
            const isCollapsed = childContainer.classList.toggle('collapsed');
            icon.innerHTML = isCollapsed ? closedFolder : openFolder;
            element.classList.toggle('expanded', !isCollapsed);
        }
    },
    
    /**
     * Render recent folders list
     */
    renderRecentFolders() {
        const container = document.getElementById('recentFolders');
        const recent = AppState.workspace.recentPaths || [];
        
        if (!recent || recent.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 12px;">No recent folders</p>';
            return;
        }
        
        // Filter out any null/undefined paths and escape for HTML
        const validPaths = recent.filter(p => p && typeof p === 'string');
        
        if (validPaths.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 12px;">No recent folders</p>';
            return;
        }
        
        const folderIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>';
        container.innerHTML = validPaths.map(path => {
            const escapedPath = path.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            return `
                <div class="workspace-path" onclick="Workspace.selectRecentFolder('${escapedPath}')" style="margin-bottom: 8px;">
                    <span class="workspace-path-icon">${folderIcon}</span>
                    <span class="workspace-path-text">${Utils.shortenPath(path)}</span>
                </div>
            `;
        }).join('');
    },
    
    /**
     * Select a recent folder
     */
    selectRecentFolder(path) {
        document.getElementById('workspaceInput').value = path;
    },
    
    /**
     * Refresh file tree
     */
    async refresh() {
        if (AppState.workspace.currentPath) {
            await this.loadFileTree(AppState.workspace.currentPath);
        }
    }
};
