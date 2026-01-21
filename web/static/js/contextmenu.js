/**
 * DuilioCode Studio - Context Menu Module
 * Right-click context menu for file tree
 */

const ContextMenu = {
    target: null,
    
    /**
     * Show context menu
     */
    show(event) {
        // Only for file tree items
        const treeItem = event.target.closest('.tree-item');
        if (!treeItem) {
            this.hide();
            return;
        }
        
        event.preventDefault();
        
        this.target = {
            path: treeItem.dataset.path,
            isDir: treeItem.dataset.isDir === 'true'
        };
        
        const menu = document.getElementById('contextMenu');
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        menu.classList.add('active');
    },
    
    /**
     * Hide context menu
     */
    hide() {
        const menu = document.getElementById('contextMenu');
        if (menu) {
            menu.classList.remove('active');
        }
        this.target = null;
    },
    
    /**
     * New file action
     */
    newFile() {
        if (this.target && this.target.isDir) {
            FileManager.createNew(this.target.path);
        }
        this.hide();
    },
    
    /**
     * New folder action
     */
    newFolder() {
        if (this.target && this.target.isDir) {
            FileManager.createNewFolder(this.target.path);
        }
        this.hide();
    },
    
    /**
     * Rename action
     */
    rename() {
        if (this.target) {
            const newName = prompt('Enter new name:', this.target.path.split('/').pop());
            if (newName) {
                // TODO: Implement rename API
                alert('Rename not yet implemented');
            }
        }
        this.hide();
    },
    
    /**
     * Copy path action
     */
    copyPath() {
        if (this.target) {
            navigator.clipboard.writeText(this.target.path);
            Utils.showNotification('Path copied to clipboard', 'success');
        }
        this.hide();
    },
    
    /**
     * Delete action
     */
    delete() {
        if (this.target) {
            FileManager.delete(this.target.path);
        }
        this.hide();
    }
};
