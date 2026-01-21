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
            AppState.setWorkspace({
                currentPath: data.path,
                recentPaths: data.recent_paths || [],
                homeDirectory: data.home_directory
            });
            
            if (data.path) {
                document.getElementById('workspacePathText').textContent = Utils.shortenPath(data.path);
                await this.loadFileTree(data.path);
            }
        } catch (error) {
            console.error('Failed to load workspace:', error);
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
            AppState.setWorkspace({
                currentPath: data.path,
                recentPaths: data.recent_paths || []
            });
            
            document.getElementById('workspacePathText').textContent = Utils.shortenPath(data.path);
            await this.loadFileTree(data.path);
            this.closeModal();
        } catch (error) {
            alert('Error: ' + error.message);
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
            
            const icon = item.is_directory ? '📁' : Utils.getFileIcon(item.name);
            
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
     * Toggle folder expansion
     */
    toggleFolder(element, item) {
        const childId = `children-${item.path.replace(/[^a-zA-Z0-9]/g, '_')}`;
        const childContainer = document.getElementById(childId);
        
        if (childContainer) {
            childContainer.classList.toggle('collapsed');
            const icon = element.querySelector('.tree-item-icon');
            icon.textContent = childContainer.classList.contains('collapsed') ? '📁' : '📂';
        }
    },
    
    /**
     * Render recent folders list
     */
    renderRecentFolders() {
        const container = document.getElementById('recentFolders');
        const recent = AppState.workspace.recentPaths || [];
        
        if (recent.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 12px;">No recent folders</p>';
            return;
        }
        
        container.innerHTML = recent.map(path => `
            <div class="workspace-path" onclick="Workspace.selectRecentFolder('${path}')" style="margin-bottom: 8px;">
                <span class="workspace-path-icon">📂</span>
                <span class="workspace-path-text">${Utils.shortenPath(path)}</span>
            </div>
        `).join('');
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
